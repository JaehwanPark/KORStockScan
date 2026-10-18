import io
import json
from collections import Counter

import pytest

from src.engine.automation.main_stop_source_projection import classify_disjoint_event
from src.engine.automation.main_stop_postclose import source_events
from src.engine.automation import main_stop_source_projection as projection


def test_large_valid_disjoint_source_is_validated_without_stop_contamination(tmp_path):
    body = json.dumps({'stage': 'entry_ai_economic_plan_observed',
                       'fields': {'plan': 'quoted " text \\ ' * 180000}})
    path = tmp_path / 'mixed.jsonl'
    path.write_text(body + '\n' + json.dumps({'stage': 'main_stop_source', 'fields': {}}) + '\n')
    counts = Counter()
    rows = list(source_events(path, counts, references=True))
    assert len(rows) == 1
    assert counts['oversized_raw_rows'] == 1
    assert counts['isolated_disjoint_oversized_rows'] == 1
    assert counts['unidentifiable_raw_rows'] == 0
    assert counts['isolated_disjoint_oversized_bytes'] == len((body + '\n').encode())
    assert any(k.startswith('isolated_oversized_set_sha256:') for k in counts)


@pytest.mark.parametrize('text', [
    '{"stage":"entry_ai_economic_plan_observed","x":"bad\\q"}',
    '{"stage":"entry_ai_economic_plan_observed","x":"bad\\u00q0"}',
    '{"stage":"entry_ai_economic_plan_observed","x":[1,]}',
    '{"stage":"entry_ai_economic_plan_observed","x":bad}',
    '{"stage":"entry_ai_economic_plan_observed","x":NaN}',
    '{"stage":"entry_ai_economic_plan_observed","stage":"unknown"}',
    '{"stage":"entry_ai_economic_plan_observed","x":{"a":1,"a":2}}',
    '{"stage":"entry_ai_economic_plan_observed"} false',
    '{"stage":"entry_ai_economic_plan_observed","fields":null}',
])
def test_malformed_full_json_cannot_be_an_exclusion_receipt(text):
    with pytest.raises(ValueError):
        classify_disjoint_event(io.StringIO(text))


def test_stage_substring_or_stop_field_never_proves_disjoint_scope():
    for value in (
        {'stage': 'unknown', 'fields': {}},
        {'text': 'entry_ai_economic_plan_observed'},
        {'stage': 'entry_ai_economic_plan_observed', 'fields': {'main_stop_source': '{}'}},
        {'stage': 'main_stop_source', 'fields': {'body': 'unrelated'}},
    ):
        assert classify_disjoint_event(io.StringIO(json.dumps(value))) is None


def test_damaged_oversized_entry_keeps_global_source_gap(tmp_path):
    path = tmp_path / 'mixed.jsonl'
    path.write_text('{"stage":"entry_ai_economic_plan_observed","fields":{"x":"' +
                    'x' * (2 * 1024 * 1024) + '\\q"}}\n')
    census = Counter()
    assert list(source_events(path, census)) == []
    assert census['unidentifiable_raw_rows'] == 1
    assert census['isolated_disjoint_oversized_rows'] == 0


@pytest.mark.parametrize('space', ['\v', '\f', '\u00a0', '\u2028'])
@pytest.mark.parametrize('nested', [False, True])
def test_only_json_whitespace_can_establish_disjoint_scope(space, nested):
    text = ('{"stage":"entry_ai_economic_plan_observed",' + space + '"fields":{}}'
            if not nested else '{"stage":"entry_ai_economic_plan_observed","fields":{"x":[1,' + space + '2]}}')
    with pytest.raises(ValueError):
        classify_disjoint_event(io.StringIO(text))


class ChunkedInput(io.StringIO):
    def __init__(self, text, chunk):
        super().__init__(text)
        self.chunk = chunk

    def read(self, size=-1):
        return super().read(self.chunk if size < 0 else min(size, self.chunk))


@pytest.mark.parametrize('chunk', [1, 2, 7, 65536])
def test_escape_and_number_boundaries_preserve_whole_json_validation(chunk):
    value = dict(stage='entry_ai_economic_plan_observed', fields={
        'complex': [{'x': 'brace } quote " backslash \\ unicode 한글 \n\t'}] * 11,
        'numbers': [12345678901234567890, -123.456e-20, True, None]})
    text = json.dumps(value)
    assert classify_disjoint_event(ChunkedInput(text, chunk)) == value['stage']
    with pytest.raises(ValueError):
        classify_disjoint_event(ChunkedInput(text.replace('backslash ', 'bad\\q'), chunk))


def test_active_nested_key_budget_is_shared_and_released(monkeypatch):
    monkeypatch.setattr(projection, 'ACTIVE_KEY_BYTES_LIMIT', 16)
    valid = dict(stage='entry_ai_economic_source_gap', fields={
        'x': [{'long': 1}, {'long': 2}]})
    assert classify_disjoint_event(io.StringIO(json.dumps(valid))) == valid['stage']
    nested = dict(stage=valid['stage'], fields={'x': {'long': {'more': 1}}})
    with pytest.raises(ValueError, match='active_key_budget'):
        classify_disjoint_event(io.StringIO(json.dumps(nested)))


@pytest.mark.parametrize('field_count', [455, 459, 497])
def test_native_wide_entry_snapshot_has_complete_bounded_disjoint_projection(tmp_path, field_count):
    fields = {f'entry_observation_{i:04d}':i for i in range(field_count-3)}
    fields.update(source_stage='ai_confirmed', entry_economic_conditional_seed='s'*(1024*1024),
                  entry_economic_operating_context='c'*(1024*1024))
    row = dict(stage='scalp_entry_action_decision_snapshot', fields=fields)
    path = tmp_path/'mixed.jsonl'
    path.write_text(json.dumps(row)+'\n')
    census = Counter()
    assert list(source_events(path, census)) == []
    assert census['isolated_disjoint_oversized_rows'] == 1
    assert census['unidentifiable_raw_rows'] == 0
    assert len(fields) == field_count


@pytest.mark.parametrize('fault', ['nonfinite', 'duplicate', 'stop', 'unknown_stage', 'trailing', 'keys'])
def test_wide_snapshot_never_bypasses_whole_json_or_stop_scope_validation(tmp_path, fault):
    fields = {f'entry_observation_{i:04d}':i for i in range(457)}
    fields.update(entry_economic_conditional_seed='s'*(1024*1024),
                  entry_economic_operating_context='c'*(1024*1024))
    row = dict(stage='scalp_entry_action_decision_snapshot', fields=fields)
    if fault == 'nonfinite': fields['tail'] = float('nan')
    elif fault == 'stop': fields['main_stop_source'] = '{}'
    elif fault == 'unknown_stage': row['stage'] = 'unregistered_entry_snapshot'
    elif fault == 'keys': fields.update({f'excess_{i}':i for i in range(1025-len(fields))})
    text = json.dumps(row)
    if fault == 'duplicate': text = text[:-2] + ',"entry_observation_0000":99}}'
    elif fault == 'trailing': text += ' false'
    path = tmp_path/'mixed.jsonl'
    path.write_text(text+'\n')
    census = Counter()
    assert list(source_events(path, census)) == []
    assert census['unidentifiable_raw_rows'] == 1
    assert census['isolated_disjoint_oversized_rows'] == 0


def test_top_level_stop_field_also_prevents_disjoint_classification():
    value = dict(stage='entry_ai_economic_plan_observed', main_stop_source='{}', fields={})
    assert classify_disjoint_event(io.StringIO(json.dumps(value))) is None


def test_spool_limit_keeps_oversized_but_valid_entry_unidentified(tmp_path, monkeypatch):
    monkeypatch.setattr(projection, 'SPOOL_LIMIT', 2 * 1024 * 1024 + 128)
    path = tmp_path / 'oversized.jsonl'
    path.write_text(json.dumps(dict(stage='entry_ai_economic_plan_observed', fields={
        'x': 'x' * (2 * 1024 * 1024 + 256)})) + '\n')
    census = Counter()
    assert list(source_events(path, census)) == []
    assert census['unidentifiable_raw_rows'] == 1
    assert census['isolated_disjoint_oversized_rows'] == 0


def test_spool_reservation_obeys_shared_disk_budget(tmp_path):
    from src.engine.lifecycle import research_disk_budget as budget
    path = tmp_path / 'oversized.jsonl'
    path.write_text(json.dumps(dict(stage='entry_ai_economic_plan_observed', fields={
        'x': 'x' * (2 * 1024 * 1024)})) + '\n')
    with budget.use(tmp_path, temp_limit=projection.SPOOL_LIMIT - 1):
        with pytest.raises(ValueError, match='combined_disk_budget'):
            list(source_events(path, Counter()))


def test_parser_refills_check_deadline_without_source_gap_reclassification(tmp_path, monkeypatch):
    from src.engine.automation import main_stop_postclose as producer
    path = tmp_path / 'oversized.jsonl'
    path.write_text(json.dumps(dict(stage='entry_ai_economic_plan_observed', fields={
        'x': 'x' * (2 * 1024 * 1024)})) + '\n')
    calls = 0
    def checkpoint():
        nonlocal calls
        calls += 1
        if calls >= 6:
            raise ValueError('stop_research_deadline_exceeded')
    monkeypatch.setattr(producer, 'checkpoint', checkpoint)
    census = Counter()
    with pytest.raises(ValueError, match='stop_research_deadline_exceeded'):
        list(producer.source_events(path, census))
    assert census['unidentifiable_raw_rows'] == 0


@pytest.mark.parametrize('stage', ['main_stop_source', 'holding_path_signal_snapshot', 'unclassified'])
def test_other_oversized_scopes_stay_global_source_gaps(tmp_path, stage):
    path = tmp_path / 'oversized.jsonl'
    path.write_text(json.dumps(dict(stage=stage, fields={'x': 'x' * (2 * 1024 * 1024)})) + '\n')
    census = Counter()
    assert list(source_events(path, census)) == []
    assert census['unidentifiable_raw_rows'] == 1
    assert census['isolated_disjoint_oversized_rows'] == 0
