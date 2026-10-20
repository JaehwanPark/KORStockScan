import json
import pytest

from src.engine import buy_funnel_sentinel as buy
from src.engine import holding_exit_sentinel as holding
from src.engine.sentinel_event_cache import update_and_load_cached_event_rows

TARGET_DATE = "2026-05-06"


def test_compact_index_preserves_large_fields_and_only_parses_appends(tmp_path, monkeypatch):
    from pathlib import Path
    from src.engine.monitoring.sentinel_compact_store import CompactFields
    raw = _raw_path(tmp_path)
    text = 'original policy evidence 한글 ' * 4000
    payload = _event('10:00:00', 'ai_confirmed', fields={'large': text, 'attempt': 'a'})
    _write_lines(raw, [payload, payload])
    calls = []
    def parse(row):
        calls.append(1)
        return row
    args = dict(raw_path=raw, cache_dir=tmp_path/'cache', cache_name='indexed',
                target_date=TARGET_DATE, schema_version=1, parse_payload=parse,
                compact_index=True)
    first, meta = update_and_load_cached_event_rows(**args)
    assert len(first) == 2 and len(calls) == 2  # Distinct source positions survive.
    assert isinstance(first[0]['fields'], CompactFields)
    assert first[0]['fields']['large'] == text.strip()
    cache = Path(meta['cache_path'])
    assert cache.with_suffix('.compact.sqlite').stat().st_size < cache.stat().st_size / 2
    real_open = Path.open
    def no_cache_scan(path, mode='r', *a, **kw):
        if path == cache and mode in {'r', 'rb'}:
            pytest.fail('unchanged cache body reread')
        return real_open(path, mode, *a, **kw)
    with monkeypatch.context() as m:
        m.setattr(Path, 'open', no_cache_scan)
        second, after = update_and_load_cached_event_rows(**args)
    assert len(second) == 2 and len(calls) == 2 and not after['cache_body_rescanned']
    with raw.open('a') as f:
        f.write(json.dumps(_event('10:01:00', 'order_leg_sent', fields={'attempt': 'a'}))+'\n')
    third, after = update_and_load_cached_event_rows(**args)
    assert len(third) == 3 and len(calls) == 3 and not after['cache_body_rescanned']
    assert third[-1]['stage'] == 'order_leg_sent'


def test_compact_index_corruption_fails_then_rebuilds_from_cache(tmp_path):
    import sqlite3
    from pathlib import Path
    raw = _raw_path(tmp_path)
    _write_lines(raw, [_event('10:00:00', 'ai_confirmed')])
    args = dict(raw_path=raw, cache_dir=tmp_path/'cache', cache_name='damaged',
                target_date=TARGET_DATE, schema_version=1, parse_payload=lambda x:x,
                compact_index=True)
    _, meta = update_and_load_cached_event_rows(**args)
    with sqlite3.connect(Path(meta['cache_path']).with_suffix('.compact.sqlite')) as conn:
        conn.execute("UPDATE rows SET body='changed'")
    with pytest.raises(ValueError, match='row_corrupt'):
        update_and_load_cached_event_rows(**args)
    rows, _ = update_and_load_cached_event_rows(**args)
    assert len(rows) == 1 and rows[0]['stage'] == 'ai_confirmed'


def test_optional_index_failure_after_append_preserves_native_cursor(tmp_path, monkeypatch):
    from src.engine.monitoring import sentinel_compact_store as store
    raw = _raw_path(tmp_path)
    _write_lines(raw, [_event('10:00:00', 'ai_confirmed')])
    args = dict(raw_path=raw, cache_dir=tmp_path/'cache', cache_name='resume',
                target_date=TARGET_DATE, schema_version=1, parse_payload=lambda x:x,
                compact_index=True)
    update_and_load_cached_event_rows(**args)
    with raw.open('a') as stream:
        stream.write(json.dumps(_event('10:01:00', 'budget_pass')) + '\n')
    def fail(*a, **kw):
        raise OSError('index_disk_full')
    with monkeypatch.context() as m:
        m.setattr(store, 'indexed_rows', fail)
        with pytest.raises(OSError):
            update_and_load_cached_event_rows(**args)
    rows, meta = update_and_load_cached_event_rows(**args)
    assert len(rows) == 2 and meta['appended_cache_rows'] == 0


@pytest.mark.parametrize('damage', [None, 'malformed', 'drop', 'identity'])
def test_cache_projection_preserves_population_raw_and_failure_evidence(tmp_path, damage):
    raw = _raw_path(tmp_path)
    payload = _event('10:00:00', 'scalp_entry_action_decision_snapshot', fields={
        'source_quality_status': 'pass', 'evaluation_attempt_id': 'exact',
        'entry_economic_operating_context': 'frozen_code' * 10000,
        'entry_economic_conditional_seed': 'frozen_seed' * 10000})
    _write_lines(raw, [payload])
    args = dict(raw_path=raw, cache_dir=tmp_path/'cache', cache_name='projection',
                target_date=TARGET_DATE, schema_version=1, parse_payload=lambda x: x)
    _, before = update_and_load_cached_event_rows(**args)
    cache = tmp_path/'cache'/('projection_'+TARGET_DATE+'.jsonl')
    if damage == 'malformed':
        with cache.open('a') as f: f.write('{malformed}\n')
    frozen_raw, frozen_cache = raw.read_bytes(), cache.read_bytes()
    def project(row):
        if damage == 'drop': return None
        if damage == 'identity': return dict(row, stock_code='changed')
        return buy._slim_economic_cache_row(row)
    projected = dict(args, project_loaded_payload=project, cache_projection_version='economic_source_refs_v1')
    if damage in {'drop', 'identity'}:
        with pytest.raises(ValueError, match='projection_population_changed'):
            update_and_load_cached_event_rows(**projected)
        assert cache.read_bytes() == frozen_cache
    else:
        rows, after = update_and_load_cached_event_rows(**projected)
        assert len(rows) == 1 and after['raw_offset'] == before['raw_offset']
        assert rows[0]['fields'] == {'source_quality_status': 'pass', 'evaluation_attempt_id': 'exact'}
        if damage == 'malformed':
            assert cache.read_bytes() == frozen_cache and after['cache_projection_skip_reason']
        else:
            assert cache.stat().st_size < len(frozen_cache) / 10
            once = cache.read_bytes()
            update_and_load_cached_event_rows(**projected)
            assert cache.read_bytes() == once
    assert raw.read_bytes() == frozen_raw
    assert not list((tmp_path/'cache').glob('.sentinel-projection-*'))


def test_legacy_economic_cache_without_projection_retains_unverified_inputs():
    row = {'stage': 'entry_ai_economic_plan_observed', 'fields': {
        'entry_economic_conditional_seed': 'legacy', 'entry_economic_operating_context': 'required'}}
    assert buy._slim_economic_cache_row(row) is row


def test_maintenance_streaming_does_not_change_report_population(tmp_path):
    raw = _raw_path(tmp_path)
    _write_lines(raw, [_event('10:00:00', 'blocked_ai_score'), _event('10:01:00', 'ai_confirmed')])
    args = dict(raw_path=raw, cache_dir=tmp_path/'cache', cache_name='stream',
                target_date=TARGET_DATE, schema_version=1, parse_payload=lambda x: x,
                project_loaded_payload=buy._slim_economic_cache_row, cache_projection_version='economic_source_refs_v1')
    rows, maintenance = update_and_load_cached_event_rows(**args, load_rows=False)
    assert rows == [] and maintenance['cache_event_count'] == 2 and maintenance['materialized_event_count'] == 0
    rows, normal = update_and_load_cached_event_rows(**args)
    assert len(rows) == normal['cache_event_count'] == normal['materialized_event_count'] == 2
    assert normal['appended_cache_rows'] == 0


def _event(
    hhmmss: str,
    stage: str,
    *,
    pipeline: str = "ENTRY_PIPELINE",
    record_id: int = 1,
    fields: dict | None = None,
) -> dict:
    return {
        "schema_version": 1,
        "event_type": "pipeline_event",
        "pipeline": pipeline,
        "stage": stage,
        "stock_name": "테스트종목",
        "stock_code": "000001",
        "record_id": record_id,
        "fields": fields or {},
        "emitted_at": f"{TARGET_DATE}T{hhmmss}",
        "emitted_date": TARGET_DATE,
    }


def _raw_path(tmp_path):
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir(parents=True, exist_ok=True)
    return event_dir / f"pipeline_events_{TARGET_DATE}.jsonl"


def _write_lines(path, rows: list[dict], *, malformed: bool = False) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        if malformed:
            handle.write("{malformed-json}\n")


def _without_event_load(report: dict) -> dict:
    return {key: value for key, value in report.items() if key != "event_load"}


def test_incremental_cache_parity_for_malformed_partial_unchanged_and_appended_jsonl(
    tmp_path,
):
    raw_path = _raw_path(tmp_path)
    first = {
        "id": 1,
        "source_quality_status": "pass",
        "provenance_source": "pipeline_event",
    }
    partial = {
        "id": 2,
        "source_quality_status": "warning",
        "provenance_source": "partial_then_completed",
    }
    appended = {
        "id": 3,
        "source_quality_status": "pass",
        "provenance_source": "appended",
    }
    with raw_path.open("wb") as handle:
        handle.write(json.dumps(first).encode() + b"\n")
        handle.write(b"{malformed-json}\n")
        handle.write(json.dumps(partial).encode())

    kwargs = {
        "raw_path": raw_path,
        "cache_dir": tmp_path / "cache",
        "cache_name": "parity",
        "target_date": TARGET_DATE,
        "schema_version": 1,
        "parse_payload": lambda payload: payload,
    }
    first_rows, first_meta = update_and_load_cached_event_rows(**kwargs)

    assert first_rows == [first]
    assert first_meta["decode_errors"] == 1
    assert first_meta["appended_cache_rows"] == 1
    assert first_meta["rebuilt"] is True

    with raw_path.open("ab") as handle:
        handle.write(b"\n")
        handle.write(json.dumps(appended).encode() + b"\n")

    appended_rows, appended_meta = update_and_load_cached_event_rows(**kwargs)

    assert appended_rows == [first, partial, appended]
    assert appended_meta["appended_raw_lines"] == 2
    assert appended_meta["appended_cache_rows"] == 2
    assert appended_meta["decode_errors"] == 0
    assert appended_meta["rebuilt"] is False

    unchanged_rows, unchanged_meta = update_and_load_cached_event_rows(**kwargs)

    assert unchanged_rows == appended_rows
    assert unchanged_meta["appended_raw_lines"] == 0
    assert unchanged_meta["appended_cache_rows"] == 0
    assert unchanged_meta["decode_errors"] == 0
    assert unchanged_meta["rebuilt"] is False


def test_incremental_cache_empty_and_missing_raw_fallback(tmp_path):
    raw_path = _raw_path(tmp_path)
    raw_path.touch()
    kwargs = {
        "raw_path": raw_path,
        "cache_dir": tmp_path / "cache",
        "cache_name": "empty",
        "target_date": TARGET_DATE,
        "schema_version": 1,
        "parse_payload": lambda payload: payload,
    }

    empty_rows, empty_meta = update_and_load_cached_event_rows(**kwargs)
    assert empty_rows == []
    assert empty_meta["status"] == "ok"
    assert empty_meta["cache_event_count"] == 0

    raw_path.unlink()
    missing_rows, missing_meta = update_and_load_cached_event_rows(**kwargs)
    assert missing_rows == []
    assert missing_meta["status"] == "raw_missing"
    assert missing_meta["cache_event_count"] == 0


def test_buy_sentinel_raw_cache_report_parity(monkeypatch, tmp_path):
    monkeypatch.setattr(buy, "DATA_DIR", tmp_path)
    raw_path = _raw_path(tmp_path)
    _write_lines(
        raw_path,
        [
            _event("10:03:00", "order_bundle_submitted", record_id=3),
            _event("10:00:00", "ai_confirmed", record_id=1),
            _event(
                "10:01:00",
                "blocked_ai_score",
                record_id=2,
                fields={
                    "score": 66,
                    "source_quality_status": "pass",
                    "provenance_source": "entry_adm",
                    "actual_order_submitted": False,
                },
            ),
        ],
        malformed=True,
    )
    as_of = buy._parse_as_of(TARGET_DATE, "10:05:00")

    raw_report = buy.build_buy_funnel_sentinel_report(TARGET_DATE, as_of=as_of)
    cache_report = buy.build_buy_funnel_sentinel_report(
        TARGET_DATE, as_of=as_of, use_cache=True
    )

    assert _without_event_load(cache_report) == _without_event_load(raw_report)


def test_holding_exit_sentinel_raw_cache_report_parity(monkeypatch, tmp_path):
    monkeypatch.setattr(holding, "DATA_DIR", tmp_path)
    raw_path = _raw_path(tmp_path)
    _write_lines(
        raw_path,
        [
            _event(
                "10:03:00",
                "sell_order_sent",
                pipeline="HOLDING_PIPELINE",
                record_id=3,
                fields={"actual_order_submitted": True},
            ),
            _event(
                "10:00:00",
                "holding_started",
                pipeline="HOLDING_PIPELINE",
                record_id=1,
            ),
            _event(
                "10:01:00",
                "ai_holding_review",
                pipeline="HOLDING_PIPELINE",
                record_id=1,
                fields={
                    "ai_cache": "miss",
                    "source_quality_status": "pass",
                    "provenance_source": "holding_flow",
                },
            ),
            _event(
                "10:02:00",
                "exit_signal",
                pipeline="HOLDING_PIPELINE",
                record_id=1,
            ),
        ],
        malformed=True,
    )
    as_of = holding._parse_as_of(TARGET_DATE, "10:05:00")

    raw_report = holding.build_holding_exit_sentinel_report(TARGET_DATE, as_of=as_of)
    cache_report = holding.build_holding_exit_sentinel_report(
        TARGET_DATE, as_of=as_of, use_cache=True
    )

    assert _without_event_load(cache_report) == _without_event_load(raw_report)


def test_verified_day_facts_cold_warm_append_correction_partial_and_corruption(tmp_path):
    from src.engine.sentinel_event_cache import load_verified_day_projection
    source = tmp_path / "pipeline_events_2026-09-16.jsonl"
    cache = tmp_path / "cache"
    source.write_text('{"stage":"route","price":100}\n{"stage":"unrelated"}\n')
    parsed = []
    def project(row):
        parsed.append(row)
        return row if row["stage"] == "route" else {"_census": {"irrelevant": 1}}
    def load():
        return load_verified_day_projection(raw_path=source, cache_dir=cache,
            cache_name="day-facts", parser_version="frozen-parser-v1", parse_payload=project)
    cold, first = load()
    parsed.clear()
    warm, second = load()
    assert warm == cold and second["raw_scanned"] is False and parsed == []
    assert first["source_sha256"] == second["source_sha256"]
    with source.open("a") as handle:
        handle.write('{"stage":"route","price":101}\n')
    appended, status = load()
    assert [row["price"] for row in appended] == [100, 101] and status["raw_scanned"] is True
    import os
    before = source.stat()
    source.write_text(source.read_text().replace('"price":100', '"price":102'))
    os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
    corrected, status = load()
    assert corrected[0]["price"] == 102 and status["raw_scanned"] is True
    completed = next(cache.glob("*.json")).read_bytes()
    with source.open("a") as handle:
        handle.write('{"stage":"route","price":')
    partial, status = load()
    assert partial == corrected and status["checkpoint_complete"] is False
    assert next(cache.glob("*.json")).read_bytes() == completed
    with source.open("a") as handle:
        handle.write('103}\n')
    recovered, status = load()
    assert recovered[-1]["price"] == 103 and status["checkpoint_complete"] is True
    next(cache.glob("*.json")).write_text('{"body":{"generation":[]},"body_sha256":"bad"}')
    repaired, status = load()
    assert repaired == recovered and status["raw_scanned"] is True
    # Interrupted temporary publication is never a completed checkpoint.
    checkpoint = next(cache.glob("*.json"))
    (cache / (checkpoint.name + ".interrupted.tmp")).write_text('{"body":')
    unchanged, status = load()
    assert unchanged == recovered and status["raw_scanned"] is False
    # A concurrent retry evaluates changed input but does not overwrite the
    # other writer's checkpoint, and subsequent exclusive retry completes it.
    import fcntl
    completed = checkpoint.read_bytes()
    with checkpoint.with_suffix(".lock").open("a") as concurrent:
        fcntl.flock(concurrent, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with source.open("a") as handle:
            handle.write('{"stage":"route","price":104}\n')
        concurrent_rows, status = load()
        assert concurrent_rows[-1]["price"] == 104 and status["raw_scanned"] is True
        assert checkpoint.read_bytes() == completed
    retry, status = load()
    assert retry == concurrent_rows and status["checkpoint_complete"] is True


def test_verified_zero_stage_census_upgrades_cache_without_raw_bootstrap(tmp_path):
    from src.engine.observation_source_quality_audit import _raw_generation
    raw = _raw_path(tmp_path)
    _write_lines(raw, [_event("10:00:00", "ai_confirmed")])
    kwargs = dict(raw_path=raw, cache_dir=tmp_path / "cache", cache_name="proof",
        target_date=TARGET_DATE, schema_version=12, parse_payload=lambda payload: payload)
    original, _ = update_and_load_cached_event_rows(**kwargs)
    proof = {"from_schema": 12, "raw_generation": _raw_generation(raw),
             "population_proof": "verified_zero_stage_census", "raw_audit_sha256": "a" * 64}
    refreshed, meta = update_and_load_cached_event_rows(**{**kwargs, "schema_version": 13}, verified_schema_migration=proof)
    assert refreshed == original
    assert meta["rebuilt"] is False
    assert meta["appended_raw_lines"] == 0
    assert meta["schema_version"] == 13
    assert meta["schema_migration_receipt"] == proof
    raw.write_text(raw.read_text() + '{}\n')
    import pytest
    with pytest.raises(ValueError, match="verified_cache_schema_source_changed"):
        update_and_load_cached_event_rows(**{**kwargs, "schema_version": 13}, verified_schema_migration=proof)


def test_lossless_funnel_preserves_broker_ambiguity_stage(tmp_path):
    payload = _event("10:00:00", "order_leg_owner_registry_reconciliation_required", fields={"tag": "ENTRY-L1"})
    row = buy._payload_to_cache_row(payload, exclude_summary_stages=True)
    assert row is not None
    assert row["stage"] == "order_leg_owner_registry_reconciliation_required"


def test_forward_guard_stage_extension_preserves_prefix_without_replay(tmp_path):
    from src.engine.observation_source_quality_audit import _raw_generation
    raw = _raw_path(tmp_path)
    _write_lines(raw, [_event('10:00:00', 'ai_confirmed'),
                      _event('10:01:00', 'real_weak_pullback_entry_block')])
    args = dict(raw_path=raw, cache_dir=tmp_path/'cache', cache_name='forward',
                target_date=TARGET_DATE, schema_version=15,
                parse_payload=lambda r: r if r['stage']=='ai_confirmed' else None)
    original, old = update_and_load_cached_event_rows(**args)
    proof = {'from_schema':15, 'to_schema':17, 'raw_offset':old['raw_offset'],
             'raw_generation':_raw_generation(raw), 'population_proof':'forward_only_stage_extension',
             'historical_stage_coverage':'not_backfilled_before_raw_offset'}
    with raw.open('a') as f:
        f.write(json.dumps(_event('10:02:00','real_weak_pullback_entry_block'))+'\n')
    parsed=[]
    def parse(row):parsed.append(row);return row
    rows, meta = update_and_load_cached_event_rows(**{**args,'schema_version':17,
        'parse_payload':parse},verified_schema_migration=proof)
    assert rows[:len(original)] == original and len(rows)==2
    assert len(parsed)==1 and parsed[0]['emitted_at'].endswith('10:02:00')
    assert not meta['rebuilt'] and meta['schema_migration_receipt']==proof
    assert meta['appended_raw_lines']==1
    _, later = update_and_load_cached_event_rows(**{**args,'schema_version':17,'parse_payload':parse})
    assert later['schema_migration_receipt']['historical_stage_coverage']=='not_backfilled_before_raw_offset'


def test_forward_guard_stage_extension_rejects_replaced_source(tmp_path):
    import pytest
    from src.engine.observation_source_quality_audit import _raw_generation
    raw=_raw_path(tmp_path)
    _write_lines(raw,[_event('10:00:00','ai_confirmed')])
    args=dict(raw_path=raw,cache_dir=tmp_path/'cache',cache_name='forward',
              target_date=TARGET_DATE,schema_version=15,parse_payload=lambda row:row)
    _,old=update_and_load_cached_event_rows(**args)
    proof={'from_schema':15,'to_schema':17,'raw_offset':old['raw_offset'],
           'raw_generation':_raw_generation(raw),'population_proof':'forward_only_stage_extension',
           'historical_stage_coverage':'not_backfilled_before_raw_offset'}
    raw.unlink();_write_lines(raw,[_event('10:02:00','ai_confirmed')])
    with pytest.raises(ValueError,match='forward_cache_schema_source_changed'):
        update_and_load_cached_event_rows(**{**args,'schema_version':17},verified_schema_migration=proof)


def test_guard_stages_survive_both_sentinel_cache_modes():
    for stage in ['pre_submit_weak_context_late_entry_guard_block','real_weak_pullback_entry_block']:
        for lossless in [False,True]:
            payload=_event('10:00:00',stage,fields={'reason':'quality_guard_block'})
            assert buy._payload_to_cache_row(payload,exclude_summary_stages=lossless)['stage']==stage


def test_bounded_cache_decoder_preserves_json_semantics_and_container_isolation():
    from src.engine.sentinel_event_cache import _cache_object_decoder
    decoder = _cache_object_decoder()
    text = '{"same_field_name":{"action":"WAIT","code":"005930","missing":null,"number":1.25,"enabled":false,"rows":[1,2]},"unicode":"한글","dup":1,"dup":2}'
    first = json.loads(text, object_pairs_hook=decoder)
    second = json.loads(text, object_pairs_hook=decoder)
    assert first == second == json.loads(text)
    assert next(iter(first)) is next(iter(second))
    assert first['same_field_name']['action'] is second['same_field_name']['action']
    assert first['same_field_name'] is not second['same_field_name']
    assert first['same_field_name']['rows'] is not second['same_field_name']['rows']
    first['same_field_name']['rows'].append(3)
    assert second['same_field_name']['rows'] == [1, 2]
    # Unique data cannot make the per-read pool unbounded or change any value.
    for index in range(10000):
        expected = {f'unique_field_{index}': f'unique_value_{index}', 'long': 'x' * 1000}
        assert json.loads(json.dumps(expected), object_pairs_hook=decoder) == expected


def test_native_liquidity_stage_migration_preserves_prefix_without_replay(tmp_path, monkeypatch):
    from pathlib import Path
    raw = _raw_path(tmp_path)
    _write_lines(raw, [_event('10:00:00', 'ai_confirmed'),
                      _event('10:01:00', 'pre_submit_liquidity_guard_block')])
    cache_dir = tmp_path / 'cache'
    monkeypatch.setattr(buy, '_event_cache_dir', lambda: cache_dir)
    args = dict(raw_path=raw, cache_dir=cache_dir, cache_name=buy.EVENT_CACHE_NAME,
        target_date=TARGET_DATE, schema_version=20,
        parse_payload=lambda r: buy._payload_to_cache_row(r, exclude_summary_stages=True)
            if r['stage'] != 'pre_submit_liquidity_guard_block' else None)
    original, old = update_and_load_cached_event_rows(**args)
    prefix = Path(old['cache_path']).read_bytes()
    with raw.open('a') as stream:
        stream.write(json.dumps(_event('10:02:00', 'pre_submit_liquidity_guard_block'))+'\n')
    proof = buy._previous_cache_schema_proof(TARGET_DATE, raw, 20)
    assert proof['newly_admitted_stages'] == ['pre_submit_liquidity_guard_block']
    parsed = []
    def parse(row):
        parsed.append(row)
        return buy._payload_to_cache_row(row, exclude_summary_stages=True)
    rows, meta = update_and_load_cached_event_rows(**{**args,
        'schema_version':buy.LOSSLESS_EVENT_CACHE_SCHEMA_VERSION, 'parse_payload':parse},
        verified_schema_migration=proof)
    assert rows[:len(original)] == original and len(rows) == len(original)+1
    assert len(parsed) == 1 and rows[-1]['stage'] == 'pre_submit_liquidity_guard_block'
    assert Path(old['cache_path']).read_bytes().startswith(prefix)
    assert not meta['rebuilt'] and meta['appended_raw_lines'] == 1
    assert meta['schema_migration_receipt']['historical_stage_coverage'] == 'not_backfilled_before_raw_offset'
