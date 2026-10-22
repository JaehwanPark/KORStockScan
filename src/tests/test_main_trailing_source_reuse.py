"""Frozen input replay, native byte proofs and bounded failure paths."""
import hashlib
import json
from pathlib import Path

import pytest

from src.engine.automation import main_trailing_source_reuse as reuse
from src.engine.automation import main_trailing_source_assembler as assembler
from src.engine.automation import main_trailing_all_scope_research as research
from src.engine.automation import main_trailing_research_handoff as handoff
from src.engine.infrastructure import validation_digest_session as digests
from src.engine.lifecycle.holding_window_generation import byte_generation
from src.engine.scalping.pre_submit_delay_initial_policy import digest
from src.tests.test_main_trailing_source_assembler import fixture, DAY, TARGET, write


def approved(tmp_path, *, cost=False, indexed=False):
    data = tmp_path/'data'
    fixture(data)
    if indexed:
        from src.engine.automation import main_trailing_source_store as store
        path=data/'ai_decision_trace'/('ai_decision_trace_'+DAY+'.jsonl')
        assert store.build_step(data,path)['complete']
    if cost in ('official','invalid_official'):
        from src.tests.test_broker_cost_source import broker_fixture
        from src.tests.test_broker_cost_allocation import position
        from src.engine.lifecycle import broker_cost_allocation as allocation
        source,_,_,_=broker_fixture(data)
        receipts=allocation.build_research_cost_allocations({DAY:source},[position(1)])
        allocation.persist_research_costs(data,DAY,receipts,[DAY])
        if cost == 'invalid_official':
            from src.engine.lifecycle.broker_cost_source import source_path
            source_path(data,DAY).write_text('{"status":"source_invalid"}')
    elif cost:
        from src.engine.lifecycle.broker_cost_allocation import persist_research_costs
        persist_research_costs(data, DAY, {'1': dict(record_id='1',
            schema='initial_quantity_broker_total_allocated_cost_v1',
            status='research_cost_invalid', reason='original_cost_gap')}, [])
    origin = assembler.assemble(data, tmp_path/'original', source_date=DAY,
        target_date=TARGET, start_date=DAY, immutable=True)
    output = data/'report/main_all_scope_trailing'/DAY/'generations'/origin.parent.name
    result = research.run(origin, input_root=origin.parent, output_root=output, dry_run=False)
    report_path = output/f'research_{DAY}.json'
    extension = dict(report_path=str(report_path), report_generation=byte_generation(report_path),
        status='complete', allowed_runtime_apply=False,
        input_window_generation_sha256=result['input_window_generation_sha256'],
        scope_count=result['scope']['scope_count'],
        initial_policy_sha256=result['initial_policy']['policy_sha256'])
    holding = data/'report/monitor_snapshots'/f'holding_exit_observation_{DAY}.json'
    write(holding, dict(date=DAY, meta=dict(snapshot_profile='postclose_exit'),
        all_scope_trailing_research=extension))
    return data, origin, holding, result


@pytest.mark.parametrize('damage',[None,'old_fact','late_original_execution','missing_archive','archive_bytes'])
def test_frozen_replay_and_native_cost_reader_preserve_only_verified_later_window_append(tmp_path,damage):
    from datetime import timedelta
    from src.tests.test_broker_cost_source import broker_fixture,NOW,seal
    from src.engine.lifecycle import broker_cost_source as official
    from src.engine.lifecycle.broker_cost_reconciliation import source_generation
    from src.engine.lifecycle.holding_research_cost import Source
    data,origin,holding,original=approved(tmp_path,cost='official')
    old=official.load_source(data,DAY); raw=official.source_path(data,DAY).read_bytes()
    _,_,transport,_=broker_fixture(tmp_path/'unused')
    def later(api,payload):
        pages,meta=transport(api,payload)
        if api=='kt00015':
            pages[0]['trst_ovrl_trde_prps_array']=[{'trde_dt':'20261009','cntr_dt':'20261009','cmsn':'1'}]
        return pages,meta
    official.collect(data,DAY,transport=later,now=NOW+timedelta(days=2),refresh=True)
    archive=official.source_path(data,DAY).parent/'generations'/DAY/(old['source_sha256']+'.json')
    if damage=='missing_archive':archive.unlink()
    elif damage=='archive_bytes':archive.write_text('{}')
    elif damage:
        current=official.load_source(data,DAY)
        if damage=='old_fact':current['observations']['ka10170']['pages'][0]['tdy_trde_diary'][0]['cmsn_alm_tax']='11'
        else:current['observations']['kt00015_buy']['pages'][0]['trst_ovrl_trde_prps_array'][0]['cntr_dt']='20261008'
        seal(current);official.atomic(official.source_path(data,DAY),current)
    current=official.source_path(data,DAY).read_bytes(); holding_before=holding.read_bytes()
    manifest=reuse.prepare(data,origin,tmp_path/'reused')
    def validate():
        result=research.run(manifest,input_root=manifest.parent,output_root=tmp_path/'new-report',dry_run=False)
        value,_=reuse.sealed(manifest)
        with reuse.replay_session(value,manifest.parent):
            bound=reuse.frozen_official_source(data,official.source_path(data,DAY))
            assert bound[0].read_bytes()==raw
            assert assembler.source_generation_matches(data,DAY,official.source_path(data,DAY),bound[1])
            with Source(data) as costs:
                assert costs._read(official.source_path(data,DAY),official.MAX_BYTES)==old
                assert costs._read(official.source_path(data,DAY),official.MAX_BYTES)==old
                assert costs.sources[str(official.source_path(data,DAY))]==bound[1]
            generation=source_generation(data,DAY)
            assert generation['official_source_sha256']==hashlib.sha256(raw).hexdigest()
        return result
    if damage:
        with pytest.raises((ValueError,OSError,KeyError,reuse.InputPending)):validate()
    else:
        result=validate()
        assert result['initial_policy']==original['initial_policy']
        assert result['assembly_census']==original['assembly_census']
    assert holding.read_bytes()==holding_before
    assert official.source_path(data,DAY).read_bytes()==current
    assert source_generation(data,DAY)['official_source_sha256']==hashlib.sha256(current).hexdigest()


def test_frozen_unchanged_invalid_cost_source_retains_its_original_gap(tmp_path):
    data,origin,holding,original=approved(tmp_path,cost='invalid_official')
    before=holding.read_bytes()
    manifest=reuse.prepare(data,origin,tmp_path/'reused')
    result=research.run(manifest,input_root=manifest.parent,output_root=tmp_path/'new-report',dry_run=False)
    assert result['initial_policy']==original['initial_policy']
    assert result['assembly_census']==original['assembly_census']
    assert holding.read_bytes()==before


@pytest.mark.parametrize('damage',[None,'receipt','physical'])
def test_native_compression_metadata_is_not_an_added_research_input(tmp_path,damage):
    from src.engine.compress_db_backfilled_files import _gzip_file
    data,origin,holding,original=approved(tmp_path,indexed=True)
    raw=data/'ai_decision_trace'/('ai_decision_trace_'+DAY+'.jsonl')
    assert _gzip_file(raw,dry_run=False)[0]
    receipt=Path(str(raw)+'.gz.archive_receipt.json');physical=Path(str(raw)+'.gz')
    assert receipt.is_file() and not raw.exists()
    if damage=='receipt':receipt.write_text('{}')
    elif damage=='physical':physical.write_bytes(physical.read_bytes()+b'corrupt')
    before=holding.read_bytes()
    def validate():
        manifest=reuse.prepare(data,origin,tmp_path/'reused')
        return research.run(manifest,input_root=manifest.parent,output_root=tmp_path/'new-report',dry_run=False)
    if damage:
        with pytest.raises((ValueError,OSError,KeyError,reuse.InputPending)):validate()
    else:
        result=validate()
        assert result['initial_policy']==original['initial_policy']
        assert result['assembly_census']==original['assembly_census']
    assert holding.read_bytes()==before


@pytest.mark.parametrize('cost_revision', [False, True, 'added'])
def test_approved_normalized_input_replays_and_verifies_with_original_gaps(tmp_path, cost_revision):
    data, origin, holding, original = approved(tmp_path, cost=cost_revision is True)
    if cost_revision:
        from src.engine.lifecycle.broker_cost_allocation import persist_research_costs
        from src.engine.lifecycle.broker_cost_reconciliation import source_generation
        persist_research_costs(data, DAY, {'1': dict(record_id='1',
            schema='initial_quantity_broker_total_allocated_cost_v1',
            status='research_cost_invalid', reason='later_cost_generation')}, [])
        current_costs = source_generation(data, DAY)
        index_path = data/'runtime/initial_quantity_research_costs'/DAY/'index.json'
        current_index = index_path.read_bytes()
    before = holding.read_bytes()
    manifest = reuse.prepare(data, origin, tmp_path/'reused')
    value, _ = reuse.sealed(manifest)
    old, _ = reuse.sealed(origin)
    assert value['assembly_census'] == old['assembly_census']
    assert value['assembly_code_contract_sha256'] == old['assembly_code_contract_sha256']
    assert value['reuse_origin']['semantic_verdict_reused'] is False
    output = tmp_path/'new-report'
    current = research.run(manifest, input_root=manifest.parent, output_root=output, dry_run=False)
    checked, _ = handoff.verify_report(output/f'research_{DAY}.json', target_date=TARGET)
    assert checked == current
    assert current['initial_policy'] == original['initial_policy']
    assert current['assembly_census'] == original['assembly_census']
    assert holding.read_bytes() == before
    if cost_revision:
        assert source_generation(data, DAY) == current_costs
        assert index_path.read_bytes() == current_index
        with reuse.replay_session(value, manifest.parent):
            assert source_generation(data, DAY) != current_costs
        assert source_generation(data, DAY) == current_costs


@pytest.mark.parametrize('damage', ['missing_history', 'changed_history', 'linked_history',
    'changed_old_receipt', 'invalid_current_index', 'new_invalid_index'])
def test_frozen_cost_revision_never_admits_missing_changed_or_unbound_bytes(tmp_path, damage):
    from src.engine.lifecycle import broker_cost_allocation as costs
    data, origin, _, _ = approved(tmp_path, cost=damage != 'new_invalid_index')
    index = data/'runtime/initial_quantity_research_costs'/DAY/'index.json'
    old = json.loads(index.read_bytes()) if index.exists() else None
    history = index.parent/'index_generations'/(hashlib.sha256(index.read_bytes()).hexdigest()+'.json') if index.exists() else None
    costs.persist_research_costs(data, DAY, {'1': dict(record_id='1',
        schema='initial_quantity_broker_total_allocated_cost_v1',
        status='research_cost_invalid', reason='later_cost_generation')}, [])
    if damage == 'missing_history': history.unlink()
    elif damage == 'changed_history': history.write_text('{}')
    elif damage == 'linked_history':
        target = tmp_path/'alias.json';history.rename(target);history.symlink_to(target)
    elif damage in {'invalid_current_index', 'new_invalid_index'}: index.write_text('{}')
    else: (index.parent/'generations'/(old['receipts']['1']+'.json')).write_text('{}')
    with pytest.raises((ValueError, KeyError, OSError, reuse.InputPending)):
        manifest = reuse.prepare(data, origin, tmp_path/'reused')
        research.run(manifest, input_root=manifest.parent, output_root=tmp_path/'report', dry_run=False)


@pytest.mark.parametrize('damage', ['holding', 'manifest', 'binding', 'partition'])
def test_reuse_does_not_bypass_original_or_current_seals(tmp_path, damage):
    data, origin, holding, _ = approved(tmp_path)
    manifest = reuse.prepare(data, origin, tmp_path/'reused')
    value, _ = reuse.sealed(manifest)
    if damage == 'holding':
        holding.write_text('{}')
    elif damage == 'manifest':
        old, _ = reuse.sealed(origin)
        old['as_of'] += 1
        old.pop('artifact_sha256'); old['artifact_sha256'] = digest(old)
        write(origin, old)
    elif damage == 'binding':
        value['reuse_origin']['original_extraction_code_contract'] = '0'*64
        value.pop('artifact_sha256'); value['artifact_sha256'] = digest(value)
        write(manifest, value)
    else:
        from src.engine.lifecycle import research_storage as storage
        part = next(storage.iter_tree(manifest.parent, value['partitions_ref']))
        (manifest.parent/part['path']).write_text('{}')
    with pytest.raises((ValueError, KeyError)):
        research.run(manifest, input_root=manifest.parent, output_root=tmp_path/'bad', dry_run=False)


def test_large_unproved_source_is_pending_before_any_raw_read(tmp_path, monkeypatch):
    data, origin, _, _ = approved(tmp_path)
    path = data/'pipeline_events/pipeline_events_2026-10-08.jsonl'
    path.parent.mkdir(exist_ok=True)
    with path.open('wb') as handle:
        handle.truncate(200*1024**3)
    # Test a native catalog containing a newly discovered unproved large file.
    catalog = dict(source_date=DAY, unproved_bytes=path.stat().st_size,
        unproved=[dict(path=str(path), size=path.stat().st_size)], proofs={})
    monkeypatch.setattr(reuse, 'collect_proofs', lambda *args: catalog)
    original_open = Path.open
    def guard(self, *args, **kwargs):
        if self == path:
            pytest.fail('normal replay opened unproved 200 GiB source')
        return original_open(self, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', guard)
    with pytest.raises(reuse.InputPending, match='native_source_proof_missing'):
        with reuse.proof_session(data, origin):
            pytest.fail('unproved source admitted')


def test_native_proof_reuses_digest_but_mutation_never_falls_back_to_full_read(tmp_path, monkeypatch):
    path = tmp_path/'native-source.jsonl'; path.write_bytes(b'original')
    generation = byte_generation(path); metadata = reuse.file_stat(path)
    with digests.postclose_session(tmp_path, DAY) as session:
        session.admit_native_generation(path, generation, metadata, proof_sha256='a'*64)
        original_open = Path.open
        def guard(self, *args, **kwargs):
            if self == path:
                pytest.fail('native proof fell back to raw read')
            return original_open(self, *args, **kwargs)
        monkeypatch.setattr(Path, 'open', guard)
        assert byte_generation(path) == generation
        # Use a native descriptor to change identity without calling Path.open.
        with open(path, 'ab') as handle:
            handle.write(b'changed')
        with pytest.raises(digests.ValidationDeferred, match='proof_epoch_changed'):
            byte_generation(path)
    assert session.stats['full_reads'] == 0


def test_native_proof_rejects_wrong_identity_or_source_binding(tmp_path):
    path = tmp_path/'source'; path.write_text('original')
    generation = byte_generation(path)
    with digests.postclose_session(tmp_path, DAY) as session:
        for gen, metadata in [(dict(generation, path='other'), reuse.file_stat(path)),
                (generation, [0]*5), (dict(generation, sha256='invalid'), reuse.file_stat(path))]:
            with pytest.raises(ValueError, match='changed_or_unbound'):
                session.admit_native_generation(path, gen, metadata, proof_sha256='a'*64)


def test_native_read_budget_rejects_new_large_files_without_opening(tmp_path, monkeypatch):
    path = tmp_path/'large'
    with path.open('wb') as handle:
        handle.truncate(200*1024**3)
    with digests.postclose_session(tmp_path, DAY) as session:
        session.native_read_budget = dict(remaining=32*1024**2)
        original_open = Path.open
        def guard(self, *args, **kwargs):
            if self == path:
                pytest.fail('budget rejected too late')
            return original_open(self, *args, **kwargs)
        monkeypatch.setattr(Path, 'open', guard)
        with pytest.raises(digests.ValidationDeferred, match='read_budget_exceeded'):
            byte_generation(path)


@pytest.mark.parametrize('change', ['unchanged', 'historical_change', 'physical_conflict'])
def test_logical_vote_and_physical_source_have_separate_proof_contracts(tmp_path, change):
    from src.engine.lifecycle import research_storage as storage
    from src.tests.test_main_trailing_source_assembler import _native_inventory_vote
    data, origin, _, _ = approved(tmp_path)
    path, row = _native_inventory_vote(data, DAY)
    logical = assembler.historical_vote_generation(path, DAY)
    physical = byte_generation(path)
    value, _ = reuse.sealed(origin)
    inventory = list(storage.iter_tree(origin.parent, value['assembly_inventory_ref']))
    sources = list(storage.iter_tree(origin.parent, value['source_generations_ref']))
    inventory.append(dict(path=str(path), generation=logical))
    sources.append(dict(path=str(path), generation=physical))
    if change == 'physical_conflict':
        inventory.append(dict(path=str(path), generation=dict(physical, sha256='0'*64)))
    value['assembly_inventory_ref'] = storage.write_tree(origin.parent, inventory)
    value['source_generations_ref'] = storage.write_tree(origin.parent, sources)
    value.pop('artifact_sha256'); value['artifact_sha256'] = digest(value)
    write(origin, value)
    if change == 'historical_change':
        row['status'] = 'VALID'
        path.write_text(json.dumps(row)+'\n')
    if change == 'physical_conflict':
        with pytest.raises(ValueError, match='original_source_conflict'):
            reuse.collect_proofs(data, origin)
        return
    catalog = reuse.collect_proofs(data, origin)
    assert catalog['logical_sources'] == [dict(path=str(path), generation=logical)]
    assert next(r for r in catalog['unproved'] if r['path']==str(path))['generation'] == physical
    if change == 'historical_change':
        with pytest.raises(reuse.InputPending, match='logical_source_changed'):
            with reuse.proof_session(data, origin):
                pytest.fail('changed historical votes admitted')
    else:
        with reuse.proof_session(data, origin):
            assert byte_generation(path) == physical


@pytest.mark.parametrize('archived', [False,True])
def test_snapshot_native_writer_or_archive_proof_preserves_original_logical_bytes(tmp_path,monkeypatch,archived):
    from src.engine.lifecycle import research_storage as storage
    from src.engine import compress_db_backfilled_files as archiver
    data,origin,_,_=approved(tmp_path)
    path=data/'report/monitor_snapshots'/f'trade_review_{DAY}.json'
    write(path,dict(date=DAY,contents='original'))
    generation=byte_generation(path)
    if archived:
        monkeypatch.setattr(archiver,'MONITOR_SNAPSHOT_DIR',path.parent)
        assert archiver._gzip_file(path,dry_run=False)[0]
    else:
        digests.publish_native_bytes(data,path,generation)
    value,_=reuse.sealed(origin)
    rows=list(storage.iter_tree(origin.parent,value['source_generations_ref']))
    rows.append(dict(path=str(path),generation=generation))
    value['source_generations_ref']=storage.write_tree(origin.parent,rows)
    value.pop('artifact_sha256');value['artifact_sha256']=digest(value);write(origin,value)
    opened=Path.open
    def guard(self,*args,**kwargs):
        if self in {path,Path(str(path)+'.gz')}:
            pytest.fail('native byte proof reopened the large source')
        return opened(self,*args,**kwargs)
    monkeypatch.setattr(Path,'open',guard)
    with reuse.proof_session(data,origin):
        assert byte_generation(path)==generation


def test_frozen_inventory_delegates_large_future_journals_to_native_cohort_intake(tmp_path,monkeypatch):
    from src.engine.lifecycle import research_storage as storage
    data,origin,_,_=approved(tmp_path)
    manifest=reuse.prepare(data,origin,tmp_path/'reused');value,_=reuse.sealed(manifest)
    unrelated=data/'runtime/holding_path_votes'/'future.jsonl'
    unrelated.parent.mkdir(parents=True);unrelated.touch()
    original=list(storage.iter_tree(manifest.parent,value['assembly_inventory_ref']))
    seen=[]
    def intake(*args,**kwargs):
        seen.append(True);return original
    monkeypatch.setattr(assembler,'input_inventory',intake)
    real_stat=reuse.file_stat
    monkeypatch.setattr(reuse,'file_stat',lambda path:
        [0,0,200*1024**3,0,0] if Path(path)==unrelated else real_stat(path))
    reuse.verify_frozen_inventory(value,manifest.parent)
    assert seen==[True]


@pytest.mark.parametrize('route', ['canonical', 'routed', 'child_link', 'foreign_mount',
                                  'wrong_date', 'changed_seal', 'in_progress', 'missing_manifest'])
def test_native_cursor_issuer_accepts_only_the_bound_data_mount(tmp_path, route):
    data, origin, holding, _ = approved(tmp_path)
    source = data/'ai_decision_trace'/f'ai_decision_trace_{DAY}.jsonl'
    metadata = reuse.file_stat(source)
    row = dict(path=str(source), **dict(zip(
        ('device', 'inode', 'size', 'mtime_ns', 'ctime_ns'), metadata)))
    descriptor = dict(source_date=DAY, sources=[row])
    generation = digest(descriptor)
    directory = data/'report/main_market_weakness_research'/DAY/generation
    manifest = dict(schema='main_market_weakness_research_v1:source_manifest',
                    source_date=DAY, sources=[row])
    manifest['artifact_content_sha256'] = digest(manifest)
    terminal = dict(source_date=DAY, generation=generation, status='completed',
                    source_manifest_sha256=manifest['artifact_content_sha256'])
    terminal['artifact_content_sha256'] = digest(terminal)
    write(directory/'source_manifest.json', manifest)
    write(directory/'terminal.json', terminal)
    mount = data
    if route != 'canonical':
        mount = tmp_path/'release/data'; mount.parent.mkdir()
        mount.symlink_to(data if route != 'foreign_mount' else tmp_path/'foreign')
    routed = mount/directory.relative_to(data)
    if route == 'child_link':
        moved = directory.parent/'original'; directory.rename(moved)
        directory.symlink_to(moved)
    elif route == 'wrong_date':
        routed = mount/'report/main_market_weakness_research'/TARGET/generation
    elif route == 'changed_seal':
        terminal['status'] = 'failed'; write(directory/'terminal.json', terminal)
    cursor = dict(schema='main_market_weakness_research_v1:cursor', source_date=DAY,
        source_descriptor=descriptor, generation=generation,
        manifest_path=str(routed/'source_manifest.json'), terminal_path=str(routed/'terminal.json'))
    if route in {'in_progress','missing_manifest'}:
        cursor.pop('manifest_path'); cursor.pop('terminal_path')
        cursor['status']='in_progress' if route=='in_progress' else 'completed'
    write(directory.parent/'cursor.json', cursor)
    # The original SHA publication follows this native identity observation.
    original = origin.read_bytes(); origin.write_bytes(original)
    before = holding.read_bytes()
    if route == 'in_progress':
        catalog = reuse.collect_proofs(data, origin)
        assert str(source) not in catalog['proofs']
        assert catalog['unproved_bytes'] > 0
    elif route in {'canonical', 'routed'}:
        catalog = reuse.collect_proofs(data, origin)
        assert catalog['proofs'][str(source)]['kind'] == 'prior_native_identity_and_original_hash_epoch'
        assert catalog['proofs'][str(source)]['issuer_path'] == str(directory/'source_manifest.json')
    else:
        with pytest.raises((ValueError, OSError, KeyError)):
            reuse.collect_proofs(data, origin)
    assert origin.read_bytes() == original and holding.read_bytes() == before
