"""Native source publication through bounded, strictly offline stop research."""
from collections import Counter
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import time

import pytest

from src.engine.automation import main_stop_postclose as post
from src.engine.automation import main_stop_research_execution as run
from src.engine.lifecycle import main_stop_research_cost as cost
from src.engine.lifecycle import research_storage as storage
from src.engine.scalping import main_stop_policy as policy
from src.engine.scalping.main_stop_experiment import validate_experiment_v2
from src.tests.test_main_stop_policy import baseline, publication, rows


class EconomicSource:
    source_reference = {'status': 'fixture_adapter_boundary'}
    cost_generation = {'fixture': 'sealed_test_source'}
    closed = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.closed = True

    def validate_unchanged(self):
        pass


def economic_boundary(monkeypatch, *, eligible=False, grade='exact_execution'):
    """Only substitute the separately integration-tested cost adapter boundary."""
    prepared = EconomicSource()
    monkeypatch.setattr(cost, 'prepare_economic_source', lambda *args, **kwargs: prepared)

    def record(value, **kwargs):
        result = dict(schema='main_stop_research_cost_v1', economics_scope='main_stop_research_only',
            record_id=str(value['id']), status='eligible' if eligible else 'source_gap',
            reason=None if eligible else 'native_completion_missing', evidence_grade=grade,
            quantity_basis=dict(buy_qty=10, sell_qty=10, residual_qty=0),
            manual_exit=False, runtime_effect=False, custody_status='verified_registry_fill_census',
            fill_state='fully_closed', main_exit_source=dict(status='verified_native_decision_submit_chain'),
            terminal_observation=dict(code='005930'), allowed_runtime_apply=False)
        result['artifact_sha256'] = policy.digest(result)
        return result

    monkeypatch.setattr(cost, 'prepare_economic_record', record)
    return prepared


def fixture(tmp_path, monkeypatch, *, eligible=False, count=4):
    data = tmp_path/'data'
    _, native, parent, source = publication(data)
    if count != 4:
        population = (row for index in range(count)
                      for row in rows(1791766800.+index*100, index+1))
        source.write_text(''.join(json.dumps(dict(stage='main_stop_source',
            fields={'main_stop_source': row}))+'\n' for row in population))
        parents = {f'{role}|{market}': baseline() for role in policy.ROLES for market in policy.MARKETS}
        _, native = post.publish(data, '2026-10-12', '2026-10-13', parents=parents,
            parent_receipt=parent, snapshot_receipt=native['snapshot_receipt'],
            source_paths=[source], experiments={}, completed=[], economic_sources={})
    economic_boundary(monkeypatch, eligible=eligible)
    args = dict(data_root=data, output_root=tmp_path/'research', source_date='2026-10-12',
        target_date='2026-10-13', input_report=post.report_path(data, '2026-10-12'))
    return args, native


def tree_bytes(root):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob('*') if path.is_file()}


def test_native_roundtrip_streams_all_opportunities_and_keeps_policy_bytes(tmp_path, monkeypatch):
    args, _ = fixture(tmp_path, monkeypatch, eligible=True, count=20)
    before = tree_bytes(args['data_root'])
    report = run.run_research(**args)
    output = args['output_root']
    assert tree_bytes(args['data_root']) == before
    assert report['status'] == 'completed_report_only'
    assert report['position_count'] == 20 and len(report['examples']) == run.MAX_EXAMPLES
    assert 'positions' not in report
    evidence = list(storage.iter_tree(output, report['position_evidence']))
    assert len(evidence) == 20 and len({row['position_key'] for row in evidence}) == 20
    assert report['selected_policy'] is None
    assert all(report[key] is False for key in ('policy_mutated', 'actual_order_submitted',
        'actual_profit_verified', 'allowed_runtime_apply'))
    cell = report['cells']['SCANNER|REGULAR']
    assert cell['eligible_paired'] == 20
    metrics = cell['paired_metrics']['exact_execution']
    assert metrics and all(v['n'] == 20 for v in metrics.values())
    assert all(math.isfinite(v['equal_weight_avg_paired_delta_krw']) for v in metrics.values())
    assert all(v['n'] == 0 and v['mean_delta_bps'] is None
               for v in cell['paired_metrics']['broker_total_allocated'].values())
    performance = json.loads(Path(report['performance_path']).read_text())
    assert performance['status'] == 'measured'
    assert performance['unresolved_findings'] == ['live_capture_latency_not_measured']
    assert performance['metrics']['stages']['source_index_initial']['raw_decode_calls'] == 1
    assert performance['metrics']['stages']['source_index_warm']['raw_decode_calls'] == 0
    experiment = report['historical_experiment']
    assert experiment['cell'] == 'SCANNER|REGULAR'
    assert experiment['mode'] == 'historical_report_only' and experiment['allowed_runtime_apply'] is False
    assert experiment['frozen_at'] > experiment['source_end_at']
    with pytest.raises(ValueError, match='historical'):
        validate_experiment_v2(experiment, parent_sha=experiment['parent_sha256'],
            source_sha=experiment['source_sha256'], code_sha=experiment['code_sha256'])
    finalized = tree_bytes(output)
    with pytest.raises(ValueError, match='already_sealed'):
        run.run_research(**args)
    assert tree_bytes(output) == finalized


def test_source_gap_metrics_are_null_and_not_zero_edge(tmp_path, monkeypatch):
    args, _ = fixture(tmp_path, monkeypatch)
    report = run.run_research(**args)
    cell = report['cells']['SCANNER|REGULAR']
    assert cell['opportunities'] == 4 and cell['eligible_paired'] == 0
    assert cell['economic'] == {'source_gap': 4}
    for grades in cell['paired_metrics'].values():
        for metric in grades.values():
            assert metric['n'] == 0 and metric['delta_sum_krw'] is None
            assert metric['equal_weight_avg_paired_delta_krw'] is None
            assert metric['unavailable_reason'] == 'no_eligible_common_denominator'


@pytest.mark.parametrize('interruption',[ValueError,KeyboardInterrupt])
def test_interruption_retains_failure_and_reuses_native_index_and_replay(tmp_path, monkeypatch, interruption):
    args, _ = fixture(tmp_path, monkeypatch)
    prepared = economic_boundary(monkeypatch)
    source_bytes = tree_bytes(args['data_root'])
    deadline = post._DEADLINE.get()
    original = run._position_outcomes
    calls = 0

    def fail_second(*values, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise interruption('test_bounded_interruption')
        return original(*values, **kwargs)

    monkeypatch.setattr(run, '_position_outcomes', fail_second)
    with pytest.raises(interruption, match='bounded_interruption'):
        run.run_research(**args)
    assert prepared.closed and post._DEADLINE.get() == deadline
    assert tree_bytes(args['data_root']) == source_bytes
    output = args['output_root']
    failures = tree_bytes(output/'failures')
    progress = json.loads((output/'progress.json').read_text())
    assert progress['status'] == 'incomplete'
    assert progress['reason'] == interruption.__name__+':test_bounded_interruption'
    assert progress['receipt_sha256'] == policy.digest({k:v for k,v in progress.items() if k!='receipt_sha256'})
    assert progress['positions_completed'] == 1 and not (output/'report.json').exists()
    monkeypatch.setattr(run, '_position_outcomes', original)
    result = run.run_research(**args)
    assert tree_bytes(output/'failures') == failures
    performance = json.loads(Path(result['performance_path']).read_text())
    assert performance['metrics']['replay_cache_hits'] == 1
    initial = performance['metrics']['stages']['source_index_initial']
    assert initial['raw_decode_calls'] == 0 and initial['cache_state'] == 'cache_reused'
    assert result['position_count'] == 4
    assert tree_bytes(args['data_root']) == source_bytes


@pytest.mark.parametrize('location', ['inside_data', 'ancestor_data', 'symlink'])
def test_output_cannot_alias_source_or_policy(tmp_path, monkeypatch, location):
    args, _ = fixture(tmp_path, monkeypatch)
    if location == 'inside_data':
        args['output_root'] = args['data_root']/'report/research'
    elif location == 'ancestor_data':
        args['output_root'] = tmp_path
    else:
        alias = tmp_path/'alias'
        alias.symlink_to(args['data_root'], target_is_directory=True)
        args['output_root'] = alias/'research'
    before = tree_bytes(args['data_root'])
    with pytest.raises(ValueError, match='output_(must_not|symlink)'):
        run.run_research(**args)
    assert tree_bytes(args['data_root']) == before


def test_input_report_change_is_not_published(tmp_path, monkeypatch):
    args, _ = fixture(tmp_path, monkeypatch)
    prepared = economic_boundary(monkeypatch)

    def mutate():
        path = args['input_report']
        body = json.loads(path.read_text())
        body['test_revision'] = 'changed_during_execution'
        path.write_text(json.dumps(body))

    prepared.validate_unchanged = mutate
    with pytest.raises(ValueError, match='original_report_changed'):
        run.run_research(**args)
    assert prepared.closed
    assert not (args['output_root']/'report.json').exists()
    assert len(list((args['output_root']/'failures').glob('*.json'))) == 1


def test_external_cold_producer_receipt_is_bound_and_cache_reuse_is_not_cold(tmp_path, monkeypatch):
    args, native = fixture(tmp_path, monkeypatch)
    output = args['output_root']; output.mkdir()
    census = Counter()
    start, cpu, io = time.perf_counter(), time.process_time(), run._io()
    run.source_index.prepare(output, native['source_inventory'], post.source_events, census)
    measured = run._measurement(start, cpu, io)
    decoder_files = [Path(post.__file__), Path(run.source_index.__file__),
                     Path(run.source_index.__file__).with_name('main_stop_source_projection.py')]
    receipt = dict(schema='main_stop_cold_index_measurement_v1', status='completed',
        source_sha256=native['source_sha256'], source_inventory=native['source_inventory'],
        decoder_files={path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in decoder_files},
        census=dict(census), digest_session={}, allowed_runtime_apply=False, policy_mutated=False,
        **{key: measured[key] for key in ('wall_seconds', 'cpu_seconds', 'peak_rss_kib')})
    receipt['receipt_sha256'] = policy.digest(receipt)
    (output/'cold_index_measurement.json').write_text(json.dumps(receipt))
    before = (output/'cold_index_measurement.json').read_bytes()
    report = run.run_research(**args)
    performance = json.loads(Path(report['performance_path']).read_text())
    assert performance['metrics']['external_cold_index']['wall_seconds'] == receipt['wall_seconds']
    assert performance['metrics']['stages']['source_index_initial']['raw_decode_calls'] == 0
    assert (output/'cold_index_measurement.json').read_bytes() == before


@pytest.mark.parametrize('damage', ['replay_cache', 'input_receipt'])
def test_resumed_dependency_or_cache_damage_is_rejected(tmp_path, monkeypatch, damage):
    args, _ = fixture(tmp_path, monkeypatch)
    original = run._position_outcomes
    calls = 0

    def interrupt(*values, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ValueError('test_interrupt')
        return original(*values, **kwargs)

    monkeypatch.setattr(run, '_position_outcomes', interrupt)
    with pytest.raises(ValueError, match='test_interrupt'):
        run.run_research(**args)
    output = args['output_root']
    path = next((output/'replay_cache').glob('*.json')) if damage == 'replay_cache' else output/'input_receipt.json'
    body = json.loads(path.read_text()); body['tampered'] = True
    path.write_text(json.dumps(body))
    monkeypatch.setattr(run, '_position_outcomes', original)
    with pytest.raises(ValueError, match='replay_cache_invalid|resume_dependency_changed'):
        run.run_research(**args)
    assert not (output/'report.json').exists()
    assert len(list((output/'failures').glob('*.json'))) == 2


def test_exact_position_total_is_separate_and_unsealed_costs_cannot_enter():
    source = dict(record_id='1', quantity=10, item='005930_AL')
    economic = dict(schema='main_stop_research_cost_v1', economics_scope='main_stop_research_only',
        status='eligible', record_id='1', evidence_grade='exact_position_total',
        runtime_effect=False, allowed_runtime_apply=False, manual_exit=False,
        custody_status='verified_registry_fill_census', fill_state='fully_closed',
        main_exit_source=dict(status='verified_native_decision_submit_chain'),
        quantity_basis=dict(buy_qty=10, sell_qty=10, residual_qty=0), terminal_observation=dict(code='005930'))
    economic['artifact_sha256'] = policy.digest(economic)
    assert run._economic_matches_position(economic, source)
    economic['quantity_basis']['sell_qty'] = 9
    assert not run._economic_matches_position(economic, source)


@pytest.mark.parametrize('missing_exact_row',[False,True])
def test_native_normal_exit_prefix_preserves_postdecision_tail_without_interpolation(tmp_path,missing_exact_row):
    from src.tests.test_main_stop_research_replay import native_terminal_case
    from src.tests.test_main_stop_research_cost import DAY
    from src.tests.test_main_stop_policy import seal
    stock, native_rows, _ = native_terminal_case(tmp_path)
    data, costs = tmp_path/'native', tmp_path/'costs'
    original_last=native_rows[-1]
    emitted=list(native_rows[:-1] if missing_exact_row else native_rows)
    stock['exit_requested']=True
    for offset in (1,2):
        at=original_last['at']+offset
        emitted.append(policy.source_row(stock,at=at,bid=10050.,bid_qty=2,
            quote=dict(market_route='SOR',item='005930',transport_epoch=1,observed_epoch=at),
            coverage_complete=True,automatic_management_allowed=True,decision_profit_pct=.5,
            cost_model=original_last['cost_model'],vote_source=None,
            runtime_flags={key:original_last[key] for key in
                ('grace_enabled','protect_enabled','handoff_enabled','vote_max_worsen_pct')}))
    source=data/'pipeline_events'/f'pipeline_events_{DAY}.jsonl';source.parent.mkdir(parents=True)
    source.write_text(''.join(json.dumps(dict(stage='main_stop_source',fields={'main_stop_source':row}))+'\n'
                              for row in emitted))
    parent=seal(data/'parent.json',{'values':asdict(baseline())})
    snapshot=seal(data/'snapshot.json',{'date':DAY})
    parents={f'{role}|{market}':baseline() for role in policy.ROLES for market in policy.MARKETS}
    post.publish(data,DAY,'2026-10-19',parents=parents,parent_receipt=parent,
        snapshot_receipt=snapshot,source_paths=[source],experiments={},completed=[],economic_sources={})
    before=tree_bytes(data);cost_before=tree_bytes(costs)
    output=tmp_path/'research'
    report=run.run_research(data_root=data,cost_data_root=costs,output_root=output,
        source_date=DAY,target_date='2026-10-19',input_report=post.report_path(data,DAY))
    assert tree_bytes(data)==before and tree_bytes(costs)==cost_before
    evidence=list(storage.iter_tree(output,report['position_evidence']))
    assert len(evidence)==1
    row=evidence[0]
    if missing_exact_row:
        assert row['terminal_source_gap']=='stop_terminal_exact_original_decision_row_missing'
        assert row['replay_window']['kind']=='complete_native_position'
        assert row['outcomes']['parent']['modeled_net_krw'] is None
    else:
        assert row['terminal_source_gap'] is None
        assert row['replay_window']['kind']=='verified_normal_exit_prefix'
        assert row['replay_window']['end_at']==original_last['at']
        assert row['replay_window']['excluded_tail']['observations']==2
        assert row['replay_window']['source_evidence_preserved'] is True
        assert row['outcomes']['parent']['modeled_net_krw']>0
        assert row['outcomes']['grace_sec:0']['modeled_net_krw']<0
        assert row['common_modeled'] and row['economic_position_match']
        assert row['diagnostics']['counts']['observations']==6


def test_offline_cost_owner_code_change_invalidates_research_even_when_runtime_family_matches(tmp_path,monkeypatch):
    args,_=fixture(tmp_path,monkeypatch)
    prepared=economic_boundary(monkeypatch)
    original=Path.read_bytes
    changed=False
    def read(path):
        body=original(path)
        return body+b'\n# changed economic owner\n' if changed and path.name=='main_stop_research_cost.py' else body
    def invalidate():
        nonlocal changed
        changed=True
    monkeypatch.setattr(Path,'read_bytes',read)
    prepared.validate_unchanged=invalidate
    with pytest.raises(ValueError,match='code_changed_during_execution'):
        run.run_research(**args)
    assert not (args['output_root']/'report.json').exists()
    assert prepared.closed


def test_metrics_keep_common_denominator_grades_and_correct_standard_error():
    cell = dict(mixed_parent_values=False)
    source = dict(buy_basis_krw=10000.)
    def sample(delta):
        return {'parent': dict(modeled_net_krw=0., mae_pct=-1., exposure_sec=10.),
                'grace_sec:0': dict(modeled_net_krw=delta, mae_pct=-2., exposure_sec=5.)}
    for delta in (1., 3., 5., 7.):
        run._paired_metrics(cell, sample(delta), source, {'evidence_grade': 'exact_execution'}, True)
    run._paired_metrics(cell, sample(999.), source, {'evidence_grade': 'broker_total_allocated'}, True)
    run._paired_metrics(cell, sample(-999.), source, {'evidence_grade': 'exact_execution'}, False)
    run._finish_paired_metrics({'SCANNER|REGULAR': cell})
    stat = cell['paired_metrics']['exact_execution']['grace_sec:0']
    assert stat['n'] == 4 and stat['equal_weight_avg_paired_delta_krw'] == 4.
    assert stat['standard_error_krw'] == pytest.approx(math.sqrt(20/3/4))
    assert stat['mean_delta_bps'] == 4. and stat['mae_worse_count'] == 4
    assert cell['paired_metrics']['broker_total_allocated']['grace_sec:0']['n'] == 1
