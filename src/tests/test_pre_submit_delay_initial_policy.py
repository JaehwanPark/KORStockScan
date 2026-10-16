import json
from datetime import datetime
import pytest
from src.engine.scalping import pre_submit_delay_initial_policy as initial
from src.engine.scalping import pre_submit_delay_tuning as legacy
from src.tests.test_pre_submit_delay_tuning import _price_pattern_fixture


def _byte_source_fixture(tmp_path):
    import hashlib
    from src.engine.lifecycle.holding_window_generation import byte_generation
    paths = []
    for day, part, raw in [('2026-09-29', '000', b'alpha\n'),
                           ('2026-09-29', '001', b'beta\n'),
                           ('2026-10-02', '000', b'gamma\n')]:
        path = tmp_path / f'threshold_cycle/date={day}/family=pre_submit_delay/part-execution-{part}.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        paths.append(path)
    ledgers = {}
    for day in ['2026-09-29', '2026-10-02']:
        path = legacy.family_source_ledger_path(tmp_path, day)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{}')
        ledgers[day] = byte_generation(path)
    report = dict(source_date='2026-10-02', effective_date='2026-10-05',
        source_sha256=hashlib.sha256(b''.join(p.read_bytes() for p in paths)).hexdigest(),
        source_receipt=dict(schema='pre_submit_delay_input_generation_v1', through_date='2026-10-02',
            partition_generations={str(p):{'size':p.stat().st_size,
                'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths},
            ledger_generations=ledgers, isolated_dates={}))
    return paths, report


def test_source_verifier_one_read_preserves_part_whole_and_daily_prefix_hashes(tmp_path, monkeypatch):
    import hashlib
    from pathlib import Path
    paths, report = _byte_source_fixture(tmp_path)
    expected = {}
    for day in ['2026-09-29', '2026-10-02']:
        prefix = [p for p in paths if p.parent.parent.name <= 'date=' + day]
        expected[day] = {'sha256':hashlib.sha256(b''.join(p.read_bytes() for p in prefix)).hexdigest(),
                         'paths':[str(p) for p in prefix]}
    checked = []
    def ledger_issues(root, day, *, source_snapshot, pipeline_reference_only=False):
        source_snapshot.verify()
        assert source_snapshot.source['cumulative_generations'][day] == expected[day]
        assert source_snapshot.source['sha256'] == report['source_sha256']
        checked.append(day)
        return []
    monkeypatch.setattr(legacy, 'family_source_ledger_issues', ledger_issues)
    original = Path.open
    reads = []
    def tracked(path, *args, **kwargs):
        if path in paths and args and args[0] == 'rb': reads.append(path)
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', tracked)
    initial.verify_source(tmp_path, report)
    assert reads == paths
    assert checked == ['2026-09-29', '2026-10-02']


@pytest.mark.parametrize('mutation', ['none', 'archive', 'compact', 'ledger'])
def test_consumer_keeps_sealed_overlap_and_compact_bytes_without_raw_open(tmp_path, monkeypatch, mutation):
    from pathlib import Path
    from src.engine.automation.pre_submit_delay_source_ledger import seal
    from src.engine.lifecycle.holding_window_generation import byte_generation
    report, _ = build(tmp_path, monkeypatch, [{'prices':{0:10000, 30:9900}}])
    parts = list((tmp_path/'threshold_cycle').glob('date=*/family=pre_submit_delay/part-execution-*.jsonl'))
    rows = [json.loads(line) for p in parts for line in p.read_text().splitlines()]
    raw = tmp_path/'pipeline_events/pipeline_events_2026-10-02.jsonl'
    raw.parent.mkdir()
    raw.write_text(''.join(json.dumps({**r, 'event_type':'pipeline_event'})+'\n' for r in rows))
    seal(tmp_path, '2026-10-02')
    ledger = legacy.family_source_ledger_path(tmp_path, '2026-10-02')
    report['source_receipt']['ledger_generations'] = {'2026-10-02':byte_generation(ledger)}
    if mutation == 'archive': raw.unlink()
    elif mutation == 'compact': parts[0].write_text('{}\n')
    elif mutation == 'ledger': ledger.write_text('{}')
    original = Path.open
    def no_raw(path, *args, **kwargs):
        if path.parent == raw.parent:
            pytest.fail('policy consumer opened historical raw pipeline')
        return original(path, *args, **kwargs)
    with monkeypatch.context() as consumer:
        consumer.setattr(Path, 'open', no_raw)
        if mutation in {'compact', 'ledger'}:
            with pytest.raises(ValueError, match='generation_changed'):
                initial.verify_source(tmp_path, report, pipeline_reference_only=True)
        else:
            initial.verify_source(tmp_path, report, pipeline_reference_only=True)
    if mutation == 'none':
        raw.write_bytes(b'{}\n')
        with pytest.raises(ValueError, match='raw_compact_generation_changed'):
            initial.verify_source(tmp_path, report)


@pytest.mark.parametrize('mutation', ['rewrite', 'append', 'truncate', 'whole_hash', 'ledger'])
def test_single_pass_rejects_corrupt_part_whole_or_ledger(tmp_path, monkeypatch, mutation):
    paths, report = _byte_source_fixture(tmp_path)
    monkeypatch.setattr(legacy, 'family_source_ledger_issues', lambda *a, **k: [])
    if mutation == 'rewrite': paths[0].write_bytes(b'ALPHA\n')
    elif mutation == 'append': paths[0].write_bytes(paths[0].read_bytes() + b'x')
    elif mutation == 'truncate': paths[0].write_bytes(b'')
    elif mutation == 'whole_hash': report['source_sha256'] = '0' * 64
    else: legacy.family_source_ledger_path(tmp_path, '2026-09-29').write_text('{ }')
    with pytest.raises(ValueError, match='generation_changed'):
        initial.verify_source(tmp_path, report)


@pytest.mark.parametrize('mutation', ['old_part', 'new_part', 'symlink'])
def test_source_changed_during_ledger_validation_is_rejected(tmp_path, monkeypatch, mutation):
    paths, report = _byte_source_fixture(tmp_path)
    def race(*a, **kwargs):
        if mutation == 'old_part': paths[0].write_bytes(b'ALPHA\n')
        elif mutation == 'new_part': paths[0].with_name('part-execution-late.jsonl').write_bytes(b'new')
        else:
            other = paths[0].with_suffix('.other');other.write_bytes(paths[0].read_bytes())
            paths[0].unlink();paths[0].symlink_to(other)
        return []
    monkeypatch.setattr(legacy, 'family_source_ledger_issues', race)
    with pytest.raises(ValueError, match='source_(generation|inventory)_changed'):
        initial.verify_source(tmp_path, report)


@pytest.mark.parametrize('mutation', ['raw', 'gzip_alias', 'late_raw', 'ledger', 'compact_arrival'])
def test_invocation_digest_keeps_native_raw_compact_ledger_checks(tmp_path, monkeypatch, mutation):
    import gzip
    from src.engine.automation.pre_submit_delay_source_ledger import seal
    from src.engine.lifecycle.holding_window_generation import byte_generation
    from src.engine.infrastructure import validation_digest_session as D
    report, _ = build(tmp_path, monkeypatch, [{'prices':{0:10000, 30:9900}}])
    rows = [json.loads(line) for p in (tmp_path/'threshold_cycle').glob(
        'date=*/family=pre_submit_delay/part-execution-*.jsonl') for line in p.read_text().splitlines()]
    raw = tmp_path/'pipeline_events/pipeline_events_2026-10-02.jsonl'
    raw.parent.mkdir()
    raw.write_text(''.join(json.dumps({**r, 'event_type':'pipeline_event'})+'\n' for r in rows))
    seal(tmp_path, '2026-10-02')
    ledger = legacy.family_source_ledger_path(tmp_path, '2026-10-02')
    report['source_receipt']['ledger_generations'] = {'2026-10-02':byte_generation(ledger)}
    monkeypatch.setattr(D, 'MIN_BYTES', 1)
    with D.postclose_session(tmp_path, '2026-10-02') as invocation:
        initial.verify_source(tmp_path, report)
        initial.verify_source(tmp_path, report)
        assert invocation.stats['reused_reads'] > 0
        if mutation == 'raw': raw.write_bytes(raw.read_bytes() + b'{}\n')
        elif mutation == 'gzip_alias': raw.with_suffix('.jsonl.gz').write_bytes(gzip.compress(raw.read_bytes()))
        elif mutation == 'late_raw':
            from src.engine.pipeline_event_summary import _source_part_path
            _source_part_path(raw.parent, '2026-10-02', 'late').write_text('{}\n')
        elif mutation == 'ledger': ledger.write_text('{}')
        else:
            part = next((tmp_path/'threshold_cycle').glob('date=*/family=pre_submit_delay/part-execution-*.jsonl'))
            part.with_name('part-execution-new.jsonl').write_text('{}\n')
        with pytest.raises(ValueError, match='initial_delay_(raw_compact_generation_changed|source_inventory_changed)'):
            initial.verify_source(tmp_path, report)


def test_single_pass_rejects_replacement_after_open_even_with_same_bytes(tmp_path, monkeypatch):
    from pathlib import Path
    paths, report = _byte_source_fixture(tmp_path)
    replacement = paths[0].with_suffix('.replacement')
    replacement.write_bytes(paths[0].read_bytes())
    original = Path.open
    def racing(path, *args, **kwargs):
        stream = original(path, *args, **kwargs)
        if path == paths[0] and args and args[0] == 'rb': replacement.replace(path)
        return stream
    monkeypatch.setattr(Path, 'open', racing)
    with pytest.raises(ValueError, match='window_dependency_changed_during_read'):
        initial.verify_source(tmp_path, report)


def test_v2_streaming_admits_retained_fields_instead_of_full_raw_expansion(tmp_path,monkeypatch):
    from src.engine.lifecycle import research_input_budget as budget
    from src.engine.pipeline_event_summary import execution_projection_identity
    _price_pattern_fixture(tmp_path,monkeypatch,[{'prices':{0:10000,30:9900,60:9850}}])
    path=next((tmp_path/'threshold_cycle').glob('date=*/family=pre_submit_delay/part-execution-*.jsonl'))
    rows=[json.loads(line) for line in path.read_text().splitlines()]
    for row in rows:
        row['fields']['unused_note']='x'*48000
        row['execution_source_event_sha256']=execution_projection_identity(row)
    path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    expected=initial.project_rows(rows)
    before=budget.health()['used_bytes']
    monkeypatch.setattr(budget,'LIMIT_BYTES',before+1024*1024)
    with pytest.raises(ValueError,match='partition_resume_required'):
        legacy.SourceSnapshot.load('2026-10-02',tmp_path)
    snapshot=legacy.SourceSnapshot.load('2026-10-02',tmp_path,v2_minimal=True)
    assert snapshot.source['bytes_read']==path.stat().st_size
    assert initial.project_rows(snapshot.rows)==expected
    assert not any('unused_note' in row['fields'] for row in snapshot.rows)
    assert all(row['fields']['_source_fields_sha256'] for row in snapshot.rows)
    snapshot.verify('2026-10-02',tmp_path)
    snapshot.budget_claim.close()
    assert budget.health()['used_bytes']==before


def test_minimal_projection_preserves_conflict_in_unused_fields(tmp_path,monkeypatch):
    from src.engine.pipeline_event_summary import execution_projection_identity
    _price_pattern_fixture(tmp_path,monkeypatch,[{'prices':{0:10000,30:9900}}])
    path=next((tmp_path/'threshold_cycle').glob('date=*/family=pre_submit_delay/part-execution-*.jsonl'))
    rows=[json.loads(line) for line in path.read_text().splitlines()]
    conflicting=json.loads(json.dumps(rows[0]));conflicting['fields']['unused_note']='changed'
    conflicting['execution_source_event_sha256']=execution_projection_identity(conflicting)
    rows.append(conflicting);path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    snapshot=legacy.SourceSnapshot.load('2026-10-02',tmp_path,v2_minimal=True)
    assert initial.project_rows(snapshot.rows)==initial.project_rows(rows)
    assert initial.project_rows(snapshot.rows)[1]['exclusions']['commit_or_effective_pass_invalid']==1
    snapshot.budget_claim.close()


def build(tmp_path, monkeypatch, records):
    _price_pattern_fixture(tmp_path, monkeypatch, records)
    snapshot = legacy.SourceSnapshot.load("2026-10-02", tmp_path)
    report, policy = initial.build_initial(snapshot.rows, source_date="2026-10-02",
        publication_date="2026-10-03", effective_date="2026-10-05",
        source_sha256=snapshot.source["sha256"], code_contract_sha256=initial.code_contract(),
        source_receipt={'schema':'pre_submit_delay_input_generation_v1', 'through_date':'2026-10-02',
            'partition_generations':snapshot.source['partition_generations'], 'ledger_generations':{}, 'isolated_dates':{}})
    return report, policy


def test_source_qualification_precedes_split_and_full_n_is_preserved(tmp_path, monkeypatch):
    bad = [{"prices": {30: 9900}} for _ in range(21)]
    good = [{"prices": {0: 10000, 30: 9950}} for _ in range(6)]
    report, policy = build(tmp_path, monkeypatch, bad + good)
    assert report["census"]["raw_commit_n"] == 27
    assert report["census"]["p0_valid_n"] == 6
    cell = next(iter(policy["cells"].values()))
    assert cell["delay_sec"] == 30 and cell["train"]["n"] == 4 and cell["validation"]["n"] == 2
    assert cell["train"]["mean_bp"] == 50
    initial.validate(policy, report, target_date="2026-10-05")
    assert report["realized_pnl_krw"] is None


def test_future_validation_does_not_reselect_runner_up(tmp_path, monkeypatch):
    report, policy = build(tmp_path, monkeypatch, [
        {"prices": {0: 10000, 30: 9800, 60: 9900}},
        {"prices": {0: 10000, 30: 9800, 60: 9900}},
        {"prices": {0: 10000, 30: 10100, 60: 9900}},
    ])
    cell = next(iter(policy["cells"].values()))
    assert cell["comparison_delay_sec"] == 30
    assert cell["delay_sec"] == 0 and cell["selection_basis"] == "incumbent_on_unconfirmed_pattern"


def test_planned_horizon_purges_even_when_later_quotes_are_missing(tmp_path, monkeypatch):
    report, policy = build(tmp_path, monkeypatch, [
        {"offset": 0, "prices": {0: 10000, 30: 9900}},
        {"offset": 60, "prices": {0: 10000, 30: 9900}},
    ])
    assert len(report["partitions"][0]["purged_ids"]) == 1
    assert next(iter(policy["cells"].values()))["delay_sec"] is None
    assert policy["selection_status"] == "initial_baseline_immediate"


def test_single_pair_zero_baseline_and_no_pair_blocked(tmp_path, monkeypatch):
    report, policy = build(tmp_path, monkeypatch, [{"prices": {0: 10000, 30: 9900}}])
    initial.validate(policy, report)
    prepared = initial.PreparedPolicy.from_artifacts(policy, report, target_date="2026-10-05")
    assert prepared.lookup(target_date="2026-10-05", market="REGULAR")["delay_sec"] == 0
    report, policy = build(tmp_path, monkeypatch, [{"prices": {0: 10000}}])
    assert report["status"] == "blocked" and policy["runtime_apply_allowed"] is False
    with pytest.raises(ValueError):
        initial.publish(tmp_path, report, policy, expected_incumbent=None)


def test_committed_cas_crash_or_hash_tamper_never_consumes_mixed_generation(tmp_path, monkeypatch):
    report, policy = build(tmp_path, monkeypatch, [{"prices": {0: 10000, 30: 10000}}])
    pointer = initial.publish(tmp_path, report, policy, expected_incumbent=None)
    old = pointer.read_bytes()
    with pytest.raises(ValueError, match="cas_failed"):
        initial.publish(tmp_path, report, policy, expected_incumbent="b" * 64)
    assert pointer.read_bytes() == old
    report_file, _, _, _ = initial.committed_paths(tmp_path, "2026-10-02")
    report_file.write_text('{}')
    with pytest.raises(ValueError, match="artifact_invalid"):
        initial.committed_paths(tmp_path, "2026-10-02")


def test_prepared_lookup_has_no_file_io_and_handoff_accepts_zero(tmp_path, monkeypatch):
    report, policy = build(tmp_path, monkeypatch, [{"prices": {0: 10000, 30: 10000}}])
    initial.publish(tmp_path, report, policy, expected_incumbent=None)
    from src.engine.automation import runtime_policy_bootstrap as bootstrap, postclose_summary_handoff as handoff
    monkeypatch.setattr(bootstrap, "DATA_DIR", tmp_path)
    env, receipt = bootstrap._pre_submit_delay_handoff("2026-10-05")
    assert receipt["status"] == "verified_initial_timing_policy"
    assert handoff._stage_output_issues(tmp_path / "report", "2026-10-02", "pre_submit_delay") == []
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    now = datetime.fromisoformat("2026-10-05T09:00:00+09:00")
    assert legacy.prepare_runtime_policy(now=now)["status"] == "prepared"
    from pathlib import Path
    monkeypatch.setattr(Path, "read_text", lambda *a, **k: pytest.fail("warm lookup file I/O"))
    result = legacy.load_runtime_policy(now=now, decision_type={"session_bucket": "REGULAR"})
    assert result["delay_sec"] == 0 and result["policy_sha256"] == policy["policy_sha256"]


def test_same_path_enable_and_active_date_change_invalidate_prepared_policy(tmp_path, monkeypatch):
    report, policy = build(tmp_path, monkeypatch, [{"prices": {0: 10000, 30: 10000}}])
    initial.publish(tmp_path, report, policy, expected_incumbent=None)
    from src.engine.automation import runtime_policy_bootstrap as bootstrap
    monkeypatch.setattr(bootstrap, "DATA_DIR", tmp_path)
    env, _ = bootstrap._pre_submit_delay_handoff("2026-10-05")
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    now = datetime.fromisoformat("2026-10-05T09:00:00+09:00")
    monkeypatch.setenv("KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ENABLED", "false")
    assert legacy.prepare_runtime_policy(now=now)["status"] == "disabled"
    monkeypatch.setenv("KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ENABLED", "true")
    assert legacy.prepare_runtime_policy(now=now)["status"] == "prepared"
    assert legacy.load_runtime_policy(now=now)["policy_sha256"] == policy["policy_sha256"]
    monkeypatch.setenv("KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ACTIVE_DATE", "2026-10-06")
    # Hot lookup invalidates without doing disk work or applying stale delays.
    from pathlib import Path
    with monkeypatch.context() as patch:
        patch.setattr(Path, "read_text", lambda *a, **k: pytest.fail("warm lookup file I/O"))
        result = legacy.load_runtime_policy(now=now)
    assert result["delay_sec"] == 0 and result["policy_sha256"] is None
    assert legacy.prepare_runtime_policy(now=now)["status"] == "preparation_invalid"
    assert legacy._PREPARED_DELAY_KEY is None


def test_source_snapshot_reuses_decode_but_detects_same_size_rewrite(tmp_path, monkeypatch):
    build(tmp_path, monkeypatch, [{"prices": {0: 10000, 30: 10000}}])
    snapshot = legacy.SourceSnapshot.load("2026-10-02", tmp_path)
    rows, source = legacy._source_rows("2026-10-02", data_root=tmp_path, source_snapshot=snapshot)
    assert rows is snapshot.rows
    path = next((tmp_path / "threshold_cycle/date=2026-10-02/family=pre_submit_delay").glob("*.jsonl"))
    path.write_text(path.read_text().replace('"ask_price": 10000', '"ask_price": 10001', 1))
    with pytest.raises(ValueError, match="generation_changed"):
        snapshot.verify("2026-10-02", tmp_path)


def test_cached_projection_reuses_zero_source_decode_and_rejects_rewritten_source(tmp_path, monkeypatch):
    report,policy=build(tmp_path,monkeypatch,[{'prices':{0:10000,30:10000}}])
    initial.publish(tmp_path,report,policy,expected_incumbent=None)
    cached=legacy.initial_cached_projection(tmp_path,tmp_path,'2026-10-02',contract=initial.code_contract())
    assert cached is not None and cached[1][0]['pairs']=={30:0}
    from pathlib import Path
    path=next((tmp_path/'threshold_cycle/date=2026-10-02/family=pre_submit_delay').glob('*.jsonl'))
    path.write_text(path.read_text().replace('"ask_price": 10000','"ask_price": 10001',1))
    assert legacy.initial_cached_projection(tmp_path,tmp_path,'2026-10-02',contract=initial.code_contract()) is None
    with pytest.raises(ValueError,match='source_generation_changed'):
        initial.verify_source(tmp_path,report)


def test_unknown_historical_parents_cannot_authorize_positive_current_timing(tmp_path, monkeypatch):
    rows=[{'prices':{0:10000,30:9900}} for _ in range(3)]
    _price_pattern_fixture(tmp_path,monkeypatch,rows)
    snapshot=legacy.SourceSnapshot.load('2026-10-02',tmp_path)
    report,policy=initial.build_initial(snapshot.rows,source_date='2026-10-02',publication_date='2026-10-10',
        effective_date='2026-10-12',source_sha256=snapshot.source['sha256'],code_contract_sha256=initial.code_contract())
    assert report['census']['parent_compatibility_unverified_n']==3
    assert all(cell['delay_sec']==0 for cell in policy['cells'].values())
    assert all(cell['selection_basis']=='unverified_lineage_immediate_default' for cell in policy['cells'].values())


def test_multi_horizon_generation_survives_persistence_and_warm_rebuild(tmp_path, monkeypatch):
    report, policy = build(tmp_path, monkeypatch, [
        {'prices': {0: 10000, 30: 9980, 60: 9970, 120: 9950, 180: 9960}} for _ in range(3)])
    initial.publish(tmp_path, report, policy, expected_incumbent=None)
    report_path, policy_path, _, manifest = initial.committed_paths(tmp_path, '2026-10-02')
    assert initial.digest(json.loads(report_path.read_text())) == manifest['report_artifact_sha256']
    assert initial.digest(json.loads(policy_path.read_text())) == manifest['policy_artifact_sha256']
    saved, projection = legacy.initial_cached_projection(tmp_path, tmp_path, '2026-10-02',
                                                       contract=initial.code_contract())
    rebuilt_report, rebuilt_policy = initial.build_initial([], source_date='2026-10-02',
        publication_date='2026-10-03', effective_date='2026-10-05', source_sha256=saved['source_sha256'],
        code_contract_sha256=initial.code_contract(), _projected=(projection, saved['census']),
        source_receipt=saved['source_receipt'])
    assert rebuilt_report == report and rebuilt_policy == policy


def test_bad_durable_generation_does_not_replace_incumbent(tmp_path, monkeypatch):
    report, policy = build(tmp_path, monkeypatch, [{'prices': {0: 10000, 30: 9990}}])
    pointer = initial.publish(tmp_path, report, policy, expected_incumbent=None)
    original = pointer.read_bytes()
    # Use a valid second generation, then simulate corrupted durable bytes.
    changed_report, changed_policy = initial.build_initial([], source_date='2026-10-02',
        publication_date='2026-10-04', effective_date='2026-10-05', source_sha256=report['source_sha256'],
        code_contract_sha256=initial.code_contract(),
        _projected=([{**r, 'pairs': {int(k): v for k, v in r['pairs'].items()}}
                    for r in report['qualified_projection']], report['census']), source_receipt=report['source_receipt'])
    atomic = initial._atomic
    def corrupt(path, value):
        atomic(path, {} if path.name == 'report.json' else value)
    monkeypatch.setattr(initial, '_atomic', corrupt)
    with pytest.raises(ValueError, match='generation_artifact_invalid'):
        initial.publish(tmp_path, changed_report, changed_policy,
                        expected_incumbent=json.loads(original)['manifest_sha256'])
    assert pointer.read_bytes() == original
    initial.committed_paths(tmp_path, '2026-10-02')


def test_new_consumer_generation_reuses_qualified_source_and_reseals_selection(tmp_path, monkeypatch):
    report, policy = build(tmp_path, monkeypatch, [{'prices': {0:10000, 30:9990}}])
    initial.publish(tmp_path, report, policy, expected_incumbent=None)
    current = 'b'*64
    monkeypatch.setattr(initial, 'code_contract', lambda *a, **k: current)
    saved, projection = legacy.initial_cached_projection(tmp_path, tmp_path, '2026-10-02', contract=current)
    assert saved['code_contract_sha256'] != current
    def no_load(*a, **k):
        pytest.fail('unchanged source decoded for a consumer-only generation')
    monkeypatch.setattr(legacy.SourceSnapshot, 'load', no_load)
    assert legacy.main(['--date','2026-10-02','--effective-date','2026-10-05','--publication-date','2026-10-03',
                        '--initial-policy-v2','--input-root',str(tmp_path),'--output-root',str(tmp_path)]) == 0
    r, pp, _, _ = initial.committed_paths(tmp_path, '2026-10-02')
    assert json.loads(pp.read_text())['code_contract_sha256'] == current
    assert json.loads(r.read_text())['qualified_projection'] == report['qualified_projection']


def test_price_ready_requires_quantity_but_signal_anchor_does_not(tmp_path, monkeypatch):
    report, _ = build(tmp_path, monkeypatch, [{'prices': {0:10000,30:9990},
                      'commit_overrides':{'planned_qty':0}}])
    assert report['census']['qualified_pass_n'] == 0
    assert report['census']['exclusions']['price_ready_quantity_unverified'] == 1
    report, _ = build(tmp_path, monkeypatch, [{'prices': {0:10000,30:9990},
                      'commit_overrides':{'planned_qty':None,'anchor_kind':'signal_ready'}}])
    assert report['census']['qualified_pass_n'] == 1 and report['price_ready_pair_n'] == 0


@pytest.mark.parametrize('native,bound', [(True,False),(42,False),({'id':'x'},False),('native-request',True)])
def test_positive_current_policy_requires_typed_original_native_identity(tmp_path, monkeypatch,native,bound):
    _price_pattern_fixture(tmp_path,monkeypatch,[{'prices':{0:10000,30:9900},'commit_overrides':{
        'original_evaluation_attempt_id':native,'entry_mechanistic_policy_sha256':'a'*64,
        'entry_ai_soft_policy_sha256':'b'*64}} for _ in range(3)])
    snapshot=legacy.SourceSnapshot.load('2026-10-02',tmp_path)
    report,policy=initial.build_initial(snapshot.rows,source_date='2026-10-02',publication_date='2026-10-10',
        effective_date='2026-10-12',source_sha256=snapshot.source['sha256'],code_contract_sha256=initial.code_contract())
    assert report['census']['native_evaluation_unverified_n'] == (0 if bound else 3)
    assert all(cell['delay_sec'] == (30 if bound else 0) for cell in policy['cells'].values())


@pytest.mark.parametrize('fault', [None, 'handoff', 'origin', 'producer', 'other_function', 'dirty', 'source_missing'])
def test_same_day_consumer_compatibility_keeps_producers_and_original_policy_bound(tmp_path, monkeypatch, fault):
    import hashlib
    import subprocess
    from src.engine.automation import intraday_release_handoff as handoff
    a='src/engine/sniper_state_handlers.py';b='src/engine/scalping/pre_submit_delay_tuning.py';c='src/engine/scalping/pre_submit_delay_initial_policy.py'
    old={a:b'def _get_live_entry_arm():\n return 1\ndef safety():\n return False\n',
         b:b'def prepare_runtime_policy():\n return 1\ndef select():\n return 30\n',c:b'LABEL = 1\n'}
    new={**old,a:old[a].replace(b'return 1',b'return 2'),b:old[b]+b'def _verify_runtime_code_contract():\n return True\n'}
    if fault=='producer':new[c]=b'LABEL = 2\n'
    if fault=='other_function':new[a]=new[a].replace(b'return False',b'return True')
    expected=initial.digest({p:hashlib.sha256(v).hexdigest() for p,v in old.items()})
    for p,v in new.items():
        path=tmp_path/p;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(v)
    if fault=='dirty':(tmp_path/a).write_bytes(new[a]+b'# uncommitted\n')
    monkeypatch.setattr(initial,'CONTRACT_PATHS',tuple(old))
    monkeypatch.setattr(initial,'code_contract',lambda: 'new-hash')
    monkeypatch.setattr(handoff,'__file__',str(tmp_path/'src/engine/automation/intraday_release_handoff.py'))
    verifier=tmp_path/'src/engine/automation/intraday_release_handoff.py'
    verifier.parent.mkdir(parents=True,exist_ok=True);verifier.write_bytes(b'# verifier\n')
    monkeypatch.setattr(handoff,'_today',lambda *a: None)
    # This case exercises the pre-consumption verification branch. A consumed
    # receipt has a different path and does not exist in this fixture.
    monkeypatch.setattr(handoff,'_paths',lambda *a: (verifier, verifier.with_name('consumed.json')))
    monkeypatch.setattr(handoff,'_selection',lambda **kw: (tmp_path,'new'))
    monkeypatch.setattr(handoff,'verify',lambda *a: {'status':'fail' if fault=='handoff' else 'pass'})
    bound=dict(code_contract_sha256=expected,policy_sha256='policy',source_date='2026-10-08',target_date='2026-10-12')
    monkeypatch.setattr(handoff,'_read',lambda p: {'selected_release_sha':'old','pre_submit_delay_handoff':bound})
    monkeypatch.setattr(handoff,'_preopen',lambda day: {'selected_release_commit':'wrong' if fault=='origin' else 'old'})
    def read_git(cmd,**kw):
        if fault=='source_missing':raise subprocess.CalledProcessError(1,cmd)
        rev,path=cmd[-1].split(':',1)
        if path=='src/engine/automation/intraday_release_handoff.py':return b'# verifier\n'
        return (old if rev=='old' else new)[path]
    monkeypatch.setattr(subprocess,'check_output',read_git)
    policy=dict(code_contract_sha256=expected,policy_sha256='policy',source_date='2026-10-08')
    if fault:
        with pytest.raises(ValueError):legacy._verify_runtime_code_contract(policy,'2026-10-12')
    else:
        receipt=legacy._verify_runtime_code_contract(policy,'2026-10-12')
        assert receipt['status']=='verified_intraday_consumer_repair'
        assert receipt['policy_effect']=='unchanged'
        assert receipt['changed_consumer_paths']==[a,b]
        assert receipt['code_contract_sha256']==expected
