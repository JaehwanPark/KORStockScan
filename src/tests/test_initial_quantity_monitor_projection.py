"""Bounded native quantity proof publication and warm source invariants."""
import hashlib
import json
from pathlib import Path

import pytest

from src.engine.scalping import initial_quantity_monitor_projection as projection
from src.engine.scalping import initial_quantity_policy as native


def _fixture(tmp_path, monkeypatch, *, external=False):
    data = tmp_path/'data'
    base = (tmp_path/'custom-output' if external else
            data/'report/initial_entry_quantity_type_policy/refresh_postclose_2026-10-08')
    base.mkdir(parents=True)
    facts = [dict(status='HOLDING', recommendation_id=1, name='정상 거래')]
    report = dict(source_date='2026-10-08', trades=[], notes='허용된 원본',
        census=dict(input_fact_rows=facts, input_manifest_sha256=native._digest(facts),
            fact_rows_read=1, all_completed_initial_trades=0, excluded={'not_completed': 1}))
    report['report_content_sha256'] = native._digest(report)
    evaluation = dict(economic_sample_status='valid_empty', trade_policy_binding_status='valid_empty',
        source_date=report['source_date'], report_content_sha256=report['report_content_sha256'])
    paths = {}
    for name, value in (('report', report), ('evaluation', evaluation), ('timeout_research', {'original': True})):
        path = base/(name+'.json')
        raw = json.dumps(value, ensure_ascii=False).encode()
        # Legal native JSON whitespace exceeds the unchanged consumer bound.
        if name in {'report', 'timeout_research'}:
            raw += b' '*(4*1024*1024+1)
        path.write_bytes(raw)
        paths[name] = path
    body = dict(source_date='2026-10-08', generation_kind='refresh',
        all_completed_initial_trades=0, decision='carry_parent', following_bar_source_status='no_winners')
    for name, path in paths.items():
        body[name+'_path'] = str(path)
        body[name+'_file_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    body['report_content_sha256'] = report['report_content_sha256']
    stage = {**body, 'receipt_content_sha256': native._digest(body)}
    stage_path = base/'initial_quantity_refresh_stage_2026-10-08.json'
    stage_path.write_text(json.dumps(stage))
    monkeypatch.setattr(native, 'refresh_quantity_stage_terminal_valid', lambda stage: True)
    return data, stage_path, stage, report, paths


def _read(path, *, limit=1024*1024, expected_sha=None):
    value, record = projection.files._read(Path(path), limit)
    if expected_sha is not None:
        assert record['sha256'] == expected_sha
    return value


def _reseal(path, stage, report, children):
    report['report_content_sha256'] = native._digest({k:v for k,v in report.items() if k != 'report_content_sha256'})
    children['report'].write_bytes(json.dumps(report, ensure_ascii=False).encode()+b' '*(4*1024*1024+1))
    evaluation = json.loads(children['evaluation'].read_bytes())
    evaluation['report_content_sha256'] = report['report_content_sha256']
    children['evaluation'].write_text(json.dumps(evaluation))
    for name, child in children.items():
        stage[name+'_file_sha256'] = hashlib.sha256(child.read_bytes()).hexdigest()
    stage['report_content_sha256'] = report['report_content_sha256']
    stage['receipt_content_sha256'] = native._digest({k:v for k,v in stage.items() if k != 'receipt_content_sha256'})
    path.write_text(json.dumps(stage))


@pytest.mark.parametrize('external', [False, True])
def test_large_report_and_timeout_use_small_proof_without_reopening_originals(tmp_path, monkeypatch, external):
    data, path, stage, report, children = _fixture(tmp_path, monkeypatch, external=external)
    originals = {name: value.read_bytes() for name, value in children.items()}
    pointer = projection.publish(path, stage, report, data_root=data)
    assert Path(pointer['projection_path']).stat().st_size < 20000
    assert {name: value.read_bytes() for name, value in children.items()} == originals
    def bounded_reader(selected, **kwargs):
        assert Path(selected) not in {children['report'], children['timeout_research']}
        return _read(selected, **kwargs)
    observed = projection.read_verified(path, stage, read=bounded_reader, data_root=data)
    assert observed['observation']['postclose_input_fact_count'] == 1
    assert observed['observation']['postclose_stage_status'] == 'valid_empty'
    assert observed['issued']['report']['census']['input_manifest_sha256'] == native._digest(report['census']['input_fact_rows'])


@pytest.mark.parametrize('damage', ['report', 'timeout_research', 'stage', 'wrong_root', 'code', 'proof'])
def test_warm_proof_rejects_changed_sources_code_and_metadata(tmp_path, monkeypatch, damage):
    data, path, stage, report, children = _fixture(tmp_path, monkeypatch)
    pointer = projection.publish(path, stage, report, data_root=data)
    if damage in children:
        with children[damage].open('ab') as handle:
            handle.write(b' ')
    elif damage == 'stage':
        path.write_text(path.read_text()+' ')
    elif damage == 'code':
        old = projection._code()
        monkeypatch.setattr(projection, '_code', lambda: {**old, 'changed.py': 'f'*64})
    elif damage == 'proof':
        selected = Path(pointer['projection_path'])
        selected.write_text(selected.read_text()+' ')
    with pytest.raises((ValueError, AssertionError)):
        projection.read_verified(path, stage, read=_read,
            data_root=tmp_path/'foreign' if damage == 'wrong_root' else data)


def test_invalid_native_stage_and_dangling_child_never_publish_proof(tmp_path, monkeypatch):
    data, path, stage, report, children = _fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(native, 'refresh_quantity_stage_terminal_valid', lambda stage: False)
    with pytest.raises(ValueError, match='native_stage_invalid'):
        projection.publish(path, stage, report, data_root=data)
    assert not projection.manifest_path(path).exists()
    children['evaluation'].unlink()
    children['evaluation'].symlink_to(tmp_path/'missing')
    with pytest.raises(ValueError, match='symlink'):
        projection.publish(path, stage, report, data_root=data)


def test_legacy_absent_proof_is_not_generated_by_reader(tmp_path):
    assert projection.read_verified(tmp_path/'legacy.json', {}, read=_read) is None
    assert list(tmp_path.iterdir()) == []


def test_new_actual_or_research_cost_source_invalidates_warm_observation(tmp_path, monkeypatch):
    data, path, stage, report, children = _fixture(tmp_path, monkeypatch)
    from src.engine.lifecycle import broker_cost_reconciliation as costs
    actual = {'schema': 'holding_actual_cost_source_generation_v1', 'sha256': 'a'*64,
              'completion_date': '2026-10-08', 'count': 0, 'status': 'cost_source_unavailable'}
    monkeypatch.setattr(costs, 'source_generation', lambda *args, **kwargs: actual)
    report['census']['persisted_fact_generations'] = {'2026-10-08': {'cost_generation': actual}}
    _reseal(path, stage, report, children)
    projection.publish(path, stage, report, data_root=data)
    new_index = data/'runtime/initial_quantity_research_costs/2026-10-08/index.json'
    new_index.parent.mkdir(parents=True)
    new_index.write_text('{}')
    with pytest.raises(ValueError, match='cost_generation_changed'):
        projection.read_verified(path, stage, read=_read, data_root=data)


@pytest.mark.parametrize('suffix', ['.json', '.fact_projection.json', '.completed_projection.json.gz.archive_receipt.json'])
def test_canonical_completion_original_scalar_and_archive_changes_are_bound(tmp_path, monkeypatch, suffix):
    data, path, stage, report, children = _fixture(tmp_path, monkeypatch)
    report['census']['persisted_fact_generations'] = {'2026-10-08': {'issue': 'explicit_source_gap'}}
    _reseal(path, stage, report, children)
    projection.publish(path, stage, report, data_root=data)
    changed = data/'report/monitor_snapshots'/('trade_review_2026-10-08'+suffix)
    changed.parent.mkdir(parents=True)
    changed.write_text('source changed')
    with pytest.raises(ValueError, match='source_changed'):
        projection.read_verified(path, stage, read=_read, data_root=data)


def test_added_lifecycle_receipt_invalidates_even_previously_empty_directory(tmp_path, monkeypatch):
    data, path, stage, report, children = _fixture(tmp_path, monkeypatch)
    report['pipeline_source_receipts'] = {'day': {
        'path': str(data/'pipeline_events/pipeline_events_2026-10-08.jsonl'), 'sha256': 'a'*64,
        'capture_lifecycle_generation': {'source_date': '2026-10-08', 'files': []}}}
    _reseal(path, stage, report, children)
    projection.publish(path, stage, report, data_root=data)
    added = data/'runtime/initial_quantity/cap_capture_receipts/2026-10-08'/('a'*64+'.json')
    added.parent.mkdir(parents=True)
    added.write_text('{}')
    with pytest.raises(ValueError, match='lifecycle_changed'):
        projection.read_verified(path, stage, read=_read, data_root=data)


@pytest.mark.parametrize('name', ['initial_quantity_timeout.py', 'entry_split_order_plan.py', 'initial_quantity_legacy_reader.py'])
def test_transitive_native_helper_generation_changes_invalidate_proof(tmp_path, monkeypatch, name):
    data, path, stage, report, children = _fixture(tmp_path, monkeypatch)
    # Copy the actual native verifier closure and change a transitive helper's
    # bytes in that private checkout. Production source files remain untouched.
    source_root = Path(projection.__file__).resolve().parents[2]
    clone = tmp_path/'candidate/src'
    for relative in projection._code():
        target = clone/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((source_root/relative).read_bytes())
    monkeypatch.setattr(projection, '__file__', str(clone/'engine/scalping/initial_quantity_monitor_projection.py'))
    projection.publish(path, stage, report, data_root=data)
    selected = clone/'engine/scalping'/name
    selected.write_bytes(selected.read_bytes()+b'\n# private candidate correction\n')
    with pytest.raises(ValueError, match='manifest_invalid'):
        projection.read_verified(path, stage, read=_read, data_root=data)


def test_full_native_window_and_thousand_receipt_metadata_fit_existing_child_budget(tmp_path, record_property):
    from datetime import date, timedelta
    data = tmp_path/'data'
    days = [(date(2026,6,5)+timedelta(days=n)).isoformat() for n in range(256)]
    report = {'census': {'persisted_fact_generations': {day: {} for day in days}}}
    stage = {'source_date': days[-1]}
    stage_path = data/'report/stage.json'
    refs = projection._dependencies(stage_path, stage, report, data)
    assert len(refs) >= 11*256
    receipts = []
    directory = data/'runtime/initial_quantity_research_costs'/days[-1]/'generations'
    directory.mkdir(parents=True)
    for number in range(1000):
        ident = f'{number:064x}'
        (directory/(ident+'.json')).write_text('{}')
        receipts.append({'content_sha256': ident})
    generation = {'quantity_research_cost_generation': {'receipts': receipts, 'source_dates': []}}
    signature = projection._cost_signature(data, [{'source_date': days[-1], 'generation': generation}])
    encoded = projection.files._canonical({'dependencies': refs, 'cost_sources': signature})
    record_property('metadata_bytes', len(encoded))
    record_property('native_dates', 256)
    record_property('native_references', len(refs))
    record_property('cost_receipts', 1000)
    assert len(encoded) < projection.MAX_BYTES
    assert len(encoded) < 1024*1024  # Current legal structure is below 1MiB; limit retains headroom.


@pytest.mark.parametrize('correction', ['cost', 'archive', 'code'])
def test_issued_ancestry_retains_original_proof_after_live_source_or_code_corrections(tmp_path, monkeypatch, correction):
    data, path, stage, report, children = _fixture(tmp_path, monkeypatch)
    from src.engine.lifecycle import broker_cost_reconciliation as costs
    cost = {'schema': 'holding_actual_cost_source_generation_v1', 'sha256': 'a'*64,
            'completion_date': '2026-10-08', 'count': 0, 'status': 'cost_source_unavailable'}
    monkeypatch.setattr(costs, 'source_generation', lambda *args, **kwargs: cost)
    report['census']['persisted_fact_generations'] = {'2026-10-08': {'cost_generation': cost}}
    _reseal(path, stage, report, children)
    projection.publish(path, stage, report, data_root=data)
    if correction == 'cost':
        target = data/'runtime/initial_quantity_research_costs/2026-10-08/index.json'
        target.parent.mkdir(parents=True)
        target.write_text('{}')
    elif correction == 'archive':
        target = data/'report/monitor_snapshots/trade_review_2026-10-08.json.gz'
        target.parent.mkdir(parents=True)
        target.write_bytes(b'new preserved archive generation')
    else:
        old = projection._code()
        monkeypatch.setattr(projection, '_code', lambda: {**old, 'reviewed_new_native.py': 'f'*64})
    issued = projection.read_verified(path, stage, read=_read, data_root=data, role='issued_ancestry')
    assert issued['issued']['report']['census']['input_manifest_sha256'] == report['census']['input_manifest_sha256']
    with pytest.raises(ValueError):
        projection.read_verified(path, stage, read=_read, data_root=data, role='current_stage')


@pytest.mark.parametrize('child', ['report', 'timeout_research', 'evaluation', 'stage', 'proof'])
def test_issued_ancestry_still_rejects_any_declared_child_or_proof_mutation(tmp_path, monkeypatch, child):
    data, path, stage, report, children = _fixture(tmp_path, monkeypatch)
    pointer = projection.publish(path, stage, report, data_root=data)
    target = path if child == 'stage' else Path(pointer['projection_path']) if child == 'proof' else children[child]
    with target.open('ab') as handle:
        handle.write(b' ')
    with pytest.raises((ValueError, AssertionError)):
        projection.read_verified(path, stage, read=_read, data_root=data, role='issued_ancestry')


def test_issued_ancestry_rejects_child_replaced_during_bounded_stage_read(tmp_path, monkeypatch):
    data, path, stage, report, children = _fixture(tmp_path, monkeypatch)
    projection.publish(path, stage, report, data_root=data)
    def racing_read(selected, **kwargs):
        result = _read(selected, **kwargs)
        if Path(selected) == path:
            with children['timeout_research'].open('ab') as handle:
                handle.write(b' ')
        return result
    with pytest.raises(ValueError, match='issued_source_changed'):
        projection.read_verified(path, stage, read=racing_read, data_root=data, role='issued_ancestry')
