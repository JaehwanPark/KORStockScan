"""External dedup and physical/semantic evidence generations."""
import hashlib
import json
import pytest
from src.engine.lifecycle import research_storage as store
from src.engine.lifecycle.research_input_budget import health


def test_late_conflict_invalidates_earlier_record_and_retry_is_counted(tmp_path):
    with store.index(tmp_path) as db:
        store.put(db, 'x', {'value':1})
        store.put(db, 'retry', {'value':2})
        store.put(db, 'retry', {'value':2})
        store.put(db, 'x', {'value':3})
        store.put(db, 'x', {'value':1})
        assert list(store.records(db)) == [('retry', {'value':2}, 2)]
        assert list(store.records(db, conflicts=True)) == [('x', {'value':1}, 3)]
    assert not list(tmp_path.glob('.sort-*'))


def test_tree_layout_changes_physical_generation_but_not_semantics(tmp_path, monkeypatch):
    rows = [{'id':n, 'value':'x'*200} for n in range(1000)]
    monkeypatch.setattr(store, 'LEAF_BYTES', 1024)
    monkeypatch.setattr(store, 'FANOUT', 4)
    before = health()['used_bytes']
    first = store.write_tree(tmp_path/'a', iter(rows))
    assert list(store.iter_tree(tmp_path/'a', first)) == rows
    monkeypatch.setattr(store, 'LEAF_BYTES', 2048)
    second = store.write_tree(tmp_path/'b', iter(rows))
    assert list(store.iter_tree(tmp_path/'b', second)) == rows
    assert first['logical_sha256'] == second['logical_sha256']
    assert first['sha256'] != second['sha256']
    assert health()['used_bytes'] == before


def test_changed_leaf_or_count_cannot_be_accepted(tmp_path):
    ref = store.write_tree(tmp_path, [{'id':1}])
    root = json.loads((tmp_path/ref['path']).read_text())
    leaf = tmp_path/root['children'][0]['path']
    leaf.write_text(leaf.read_text().replace('"id":1', '"id":2'))
    with pytest.raises(ValueError, match='generation_changed'):
        list(store.iter_tree(tmp_path, ref))


def test_grown_shard_is_rejected_before_open_or_full_hash(tmp_path, monkeypatch):
    from pathlib import Path
    ref = store.write_tree(tmp_path, [{'id':1}])
    shard = tmp_path/ref['path']
    with shard.open('r+b') as handle:
        handle.truncate(8*1024*1024)
    def forbidden_open(*args, **kwargs):
        raise AssertionError('grown shard must fail before reading')
    monkeypatch.setattr(Path,'open',forbidden_open)
    with pytest.raises(ValueError,match='generation_changed'):
        list(store.iter_tree(tmp_path,ref))


def test_empty_tree_and_record_budget_and_cleanup_on_failure(tmp_path):
    ref = store.write_tree(tmp_path, [])
    assert ref['count'] == 0 and list(store.iter_tree(tmp_path, ref)) == []
    assert ref['logical_sha256'] == hashlib.sha256(b'').hexdigest()
    with pytest.raises(ValueError, match='record_partition_required'):
        with store.index(tmp_path) as db:
            store.put(db, 'x', {'data':'x'*(store.RECORD_BYTES+1)})
    assert not list(tmp_path.glob('.sort-*'))


def test_tree_rejects_symlink_and_temp_index_disk_overflow(tmp_path):
    root = tmp_path/'root'; root.mkdir()
    (root/'shards').symlink_to(tmp_path/'elsewhere')
    with pytest.raises(ValueError, match='path_invalid'):
        store.write_tree(root, [{'id':1}])
    with store.index(tmp_path/'index', disk_limit=16*1024) as db:
        with pytest.raises(ValueError, match='disk_budget_exceeded'):
            for n in range(100):
                store.put(db, str(n), {'data':'x'*2000})


def test_inline_and_sharded_evidence_have_identical_logic_and_tamper_checks(tmp_path):
    from copy import deepcopy
    rows=[{'id':n} for n in range(10)]
    physical=store.write_tree(tmp_path/'physical',rows)
    with store.compact_trees():inline=store.write_tree(tmp_path/'inline',rows)
    assert inline['kind']=='inline' and inline['logical_sha256']==physical['logical_sha256']
    assert list(store.iter_tree(tmp_path/'inline',inline))==rows
    for field,value in [('count',9),('size',1),('logical_sha256','a'*64),('rows',[{'id':999}])]:
        changed=deepcopy(inline);changed[field]=value
        with pytest.raises(ValueError):list(store.iter_tree(tmp_path/'inline',changed))


def test_copy_sealed_tree_preserves_generation_and_rejects_collision(tmp_path):
    from src.engine.lifecycle import research_storage as s
    source=tmp_path/'original';target=tmp_path/'published'
    ref=s.write_tree(source,({'id':i,'value':'x'*1000} for i in range(600)))
    s.copy_tree(source,target,ref)
    assert list(s.iter_tree(source,ref))==list(s.iter_tree(target,ref))
    (target/ref['path']).write_text('{}')
    with pytest.raises(ValueError,match='immutable_shard_changed'):
        s.copy_tree(source,target,ref)


def test_tree_copy_reads_each_source_once_without_separate_digest_pass(tmp_path,monkeypatch):
    from pathlib import Path
    source=tmp_path/'original';target=tmp_path/'published'
    rows=[{'id':i,'value':'x'*1000}for i in range(600)]
    ref=store.write_tree(source,rows)
    opened=[];original_open=Path.open
    def tracked_open(path,*args,**kwargs):
        if path.is_relative_to(source):opened.append(path)
        return original_open(path,*args,**kwargs)
    monkeypatch.setattr(Path,'open',tracked_open)
    monkeypatch.setattr(store,'byte_generation',lambda _:pytest.fail('copy hashed an already verified shard again'))
    store.copy_tree(source,target,ref)
    expected=set(source.glob('shards/*.json'))
    assert set(opened)==expected and len(opened)==len(expected)
    assert list(store.iter_tree(target,ref))==rows


@pytest.mark.parametrize('mutation',['source_bytes','root_count','logical_hash','target_symlink','target_oversize'])
def test_single_pass_copy_preserves_original_failure_contracts(tmp_path,mutation):
    source=tmp_path/'original';target=tmp_path/'published'
    ref=store.write_tree(source,[{'id':1}]);before=health()
    if mutation=='source_bytes':(source/ref['path']).write_text('{}')
    elif mutation=='root_count':ref={**ref,'count':9}
    elif mutation=='logical_hash':ref={**ref,'logical_sha256':'0'*64}
    else:
        destination=target/ref['path'];destination.parent.mkdir(parents=True)
        if mutation=='target_symlink':destination.symlink_to(source/ref['path'])
        else:
            with destination.open('wb')as handle:handle.truncate(8*1024*1024)
    with pytest.raises(ValueError):store.copy_tree(source,target,ref)
    assert health()==before
