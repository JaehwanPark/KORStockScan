"""Whole-population timing split and sharded producer/consumer contracts."""
import json
from pathlib import Path
import pytest
from src.engine.automation import pre_submit_delay_partitioned_research as partitioned
from src.engine.lifecycle import research_storage as storage
from src.engine.scalping import pre_submit_delay_initial_policy as initial
from src.tests.test_pre_submit_delay_initial_policy import build as legacy_build


def fixture(tmp_path, monkeypatch):
    records = [{'date':'2026-10-01' if n<14 else '2026-10-02',
                'prices':{0:10000,30:9900,60:9800,120:9900,180:9900}} for n in range(20)]
    # The source fixture spaces each opportunity by ten minutes.
    report,policy = legacy_build(tmp_path,monkeypatch,records)
    return report,policy


def build(report, output):
    return partitioned.build(report['qualified_projection'],report['census'],output_root=output,
        source_date=report['source_date'],publication_date=report['publication_date'],effective_date=report['effective_date'],
        source_sha256=report['source_sha256'],code_contract_sha256=report['code_contract_sha256'],
        source_receipt=report.get('source_receipt'))


def test_whole_split_and_metrics_equal_supported_resident_reference(tmp_path,monkeypatch):
    reference,policy = fixture(tmp_path/'source',monkeypatch)
    result,selected = build(reference,tmp_path/'result')
    cells = {r['key']:r['value'] for r in storage.iter_tree(tmp_path/'result',result['cells_ref'])}
    assert set(cells)==set(reference['cells'])
    for key,cell in cells.items():
        assert {k:v for k,v in cell.items() if k!='partition_sha256'} == {
            k:v for k,v in reference['cells'][key].items() if k!='partition_sha256'}
    initial.validate(selected,result,target_date=reference['effective_date'])
    prepared = initial.PreparedPolicy.from_artifacts(selected,result,target_date=reference['effective_date'])
    assert prepared.lookup(target_date=reference['effective_date'],market='REGULAR')['delay_sec']==60


def test_sharded_population_survives_changed_layout_and_legacy_limits(tmp_path,monkeypatch):
    report,policy = fixture(tmp_path/'source',monkeypatch)
    monkeypatch.setattr(initial,'MAX_OPPORTUNITIES',2)
    first,_ = build(report,tmp_path/'first')
    monkeypatch.setattr(storage,'LEAF_BYTES',1024)
    monkeypatch.setattr(storage,'FANOUT',3)
    second,selected = build(report,tmp_path/'second')
    for key in ('qualified_projection_ref','partitions_ref','cells_ref'):
        assert first[key]['logical_sha256']==second[key]['logical_sha256']
    assert first['qualified_projection_ref']['sha256']!=second['qualified_projection_ref']['sha256']
    initial.validate(selected,second)


def test_global_late_conflict_is_excluded_before_split(tmp_path,monkeypatch):
    report,_ = fixture(tmp_path/'source',monkeypatch)
    # New producer qualification uses the original event rows, rather than a
    # report's already-selected projection as its opportunity denominator.
    rows = [json.loads(line) for path in (tmp_path/'source/threshold_cycle').glob(
        'date=*/family=pre_submit_delay/part-execution-*.jsonl') for line in path.read_text().splitlines()]
    from src.engine.scalping.pre_submit_delay_tuning import decision_source_sha256, quote_source_sha256
    commits = [r for r in rows if r['stage']=='pre_submit_delay_committed']
    for row in commits:
        row['fields']['original_evaluation_attempt_id'] = row['fields']['delay_intent_id']
    expected, expected_counts = initial.project_rows(rows)
    original = commits[0]
    alias = json.loads(json.dumps(original))
    alias['fields']['decision_committed_at_epoch'] += 1
    alias['fields']['delay_intent_id'] += '-alias'
    alias['fields']['decision_source_sha256'] = decision_source_sha256(alias['fields'])
    with storage.index(tmp_path/'result') as db:
        census = partitioned.project(iter(rows+[alias]),db)
        assert census['qualified_pass_n']==expected_counts['qualified_pass_n']-1
        assert census['exclusions']['canonical_opportunity_conflict']==1


def test_publish_copies_only_verified_referenced_evidence_and_loader_reads_it(tmp_path,monkeypatch):
    report,_ = fixture(tmp_path/'source',monkeypatch)
    result,policy = build(report,tmp_path/'candidate')
    data=tmp_path/'published'
    pointer=initial.publish(data,result,policy,expected_incumbent=None)
    report_file,policy_file,_,manifest=initial.committed_paths(data,report['source_date'])
    durable_report,durable_policy=initial._read(report_file),initial._read(policy_file)
    initial.validate(durable_policy,durable_report)
    assert durable_report.evidence_root!=result.evidence_root
    assert manifest['report_artifact_sha256']==initial.digest(result)
    child=next((durable_report.evidence_root/'shards').glob('*.json'))
    child.write_text('{}')
    with pytest.raises(ValueError):
        initial.committed_paths(data,report['source_date'])


def test_prepared_native_raw_ledger_publishes_only_verified_evidence(tmp_path,monkeypatch):
    from src.tests.test_pre_submit_delay_tuning import _price_pattern_fixture
    from src.engine.automation.pre_submit_delay_source_ledger import seal,publish_prepared
    from src.engine.scalping import pre_submit_delay_tuning as owner
    from src.engine.infrastructure.research_release_transition import Transition
    root=tmp_path/'workspace/data';day='2026-10-02'
    _price_pattern_fixture(root,monkeypatch,[{'prices':{0:10000,30:9900}}])
    rows=[json.loads(line) for p in (root/'threshold_cycle').glob('date=*/family=pre_submit_delay/part-execution-*.jsonl') for line in p.read_text().splitlines()]
    raw=root/'pipeline_events'/f'pipeline_events_{day}.jsonl';raw.parent.mkdir()
    raw.write_text(''.join(json.dumps({**row,'event_type':'pipeline_event'})+'\n' for row in rows))
    prepared=tmp_path/'prepared';ledger=seal(root,day,output_root=prepared)
    path=prepared/owner.family_source_ledger_path(root,day).name
    assert ledger['status']=='ready' and owner.family_source_ledger_issues(root,day,ledger_path=path)==[]
    transition=Transition(root.parent,'ledger')
    with transition.owner():transition.execute([lambda:publish_prepared(root,day,path)],verify=lambda:None)
    assert owner.family_source_ledger_issues(root,day)==[]
    raw.write_text(raw.read_text()+'{}\n')
    with pytest.raises(ValueError,match='prepared_delay_ledger_invalid'):publish_prepared(root,day,path)


def test_more_than_4096_cells_retains_every_research_row_and_zero_runtime_behavior(tmp_path,monkeypatch):
    from copy import deepcopy
    reference,_=fixture(tmp_path/'source',monkeypatch)
    row=next(r for r in reference['qualified_projection'] if r['anchor_kind']=='price_ready' and r['p0_valid'])
    count=4097
    def records():
        for i in range(count):
            value=deepcopy(row);value.update(identity=initial.digest(['original',i]),situation='UNKNOWN',
                parent_compatibility=[f'unverified-parent-{i}','unverified-aux'],native_evaluation_bound=False)
            yield value
    census=dict(raw_commit_n=count,qualified_pass_n=count,p0_valid_n=count,native_evaluation_unverified_n=count,
        parent_compatibility_unverified_n=count,exclusions={})
    report,policy=partitioned.build(records(),census,output_root=tmp_path/'full',source_date='2026-10-02',
        publication_date='2026-10-10',effective_date='2026-10-12',source_sha256=reference['source_sha256'],
        code_contract_sha256=reference['code_contract_sha256'],source_receipt=reference['source_receipt'])
    assert report['qualified_projection_ref']['count']==count and report['cells_ref']['count']==count
    assert report['status']=='initial_baseline_immediate'
    prepared=initial.PreparedPolicy.from_artifacts(policy,report,target_date='2026-10-12')
    assert len(prepared.cells)==0
    assert prepared.lookup(target_date='2026-10-12',market='REGULAR',parents=['new-parent','new-aux'])['delay_sec']==0


def test_normal_native_cli_budgets_family_outputs_without_scanning_shared_raw_aliases(tmp_path,monkeypatch):
    from src.tests.test_pre_submit_delay_tuning import _price_pattern_fixture
    from src.engine.scalping import pre_submit_delay_tuning as cli
    root=tmp_path/'data'
    _price_pattern_fixture(root,monkeypatch,[{'prices':{0:10000,30:9900,60:9800}}])
    with (root/'unrelated-large-source.bin').open('wb') as handle:handle.truncate(5*1024**3)
    (root/'unrelated-raw-alias').symlink_to(tmp_path/'external-input')
    rows=[json.loads(line) for p in (root/'threshold_cycle').glob('date=*/family=pre_submit_delay/part-execution-*.jsonl') for line in p.read_text().splitlines()]
    raw=root/'pipeline_events/pipeline_events_2026-10-02.jsonl';raw.parent.mkdir()
    raw.write_text(''.join(json.dumps({**row,'event_type':'pipeline_event'})+'\n' for row in rows))
    summaries=root/'pipeline_event_summaries';summaries.mkdir()
    (summaries/'unrelated-source-alias').symlink_to(tmp_path/'external-summary')
    from src.engine.automation.pre_submit_delay_source_ledger import seal
    assert seal(root,'2026-10-02')['status']=='ready'
    assert cli.main(['--date','2026-10-02','--publication-date','2026-10-10','--effective-date','2026-10-12',
        '--initial-policy-v2','--require-family-ledger','--input-root',str(root),'--output-root',str(root)])==0
    report_file,policy_file,_,_=initial.committed_paths(root,'2026-10-02',validate_selection=False)
    report,policy=initial._read(report_file),initial._read(policy_file)
    assert report['census']['raw_commit_n']==1 and report['price_ready_pair_n']==2
    assert len(initial.PreparedPolicy.from_artifacts(policy,report,target_date='2026-10-12').cells)==0
