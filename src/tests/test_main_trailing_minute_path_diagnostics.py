"""Offline minute diagnostics consume native revisions without execution authority."""
from contextlib import closing
from datetime import datetime, timedelta
import json
from pathlib import Path
import sqlite3

import pytest

from src.engine.automation import main_trailing_minute_path_diagnostics as diagnostic
from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.holding_window_generation import byte_generation
from src.engine.scalping.pre_submit_delay_initial_policy import digest
from src.trading.market import completed_history as history


DAY = '20261015'
ISO_DAY = '2026-10-15'


def clock(value='09:10:00'):
    return datetime.fromisoformat(ISO_DAY+'T'+value+'+09:00').timestamp()


def bars(count, *, start='09:00:00', low=98, high=105):
    began = datetime.fromisoformat(ISO_DAY+'T'+start+'+09:00')
    return [dict(source_timestamp=(began+timedelta(minutes=index)).strftime('%Y%m%d%H%M%S'),
        시가=100, 고가=high, 저가=low, 현재가=101, 거래량=1000) for index in range(count)]


def publish(root, rows, *, now=None, item='005930', scope=('real','native-test'), session='unspecified', receipt_tag=None):
    now = clock() if now is None else now
    identity = history.key(scope,item,DAY,session)
    receipt = {}
    source_meta=dict(api_id='ka10080',request_code=item,rest_received_ts_ms=int(now*1000))
    if receipt_tag is not None: source_meta['test_receipt']=receipt_tag
    assert history.publish(root,identity,rows,source_meta,
        now=now,consumption_receipt=receipt)
    return root/'runtime/main_minute_history'/DAY/'completed.sqlite3', receipt


def seal(path, body):
    value = {**body,'artifact_sha256':digest(body)}
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value))
    return digest(value)


def source_manifest(tmp_path, positions=None):
    source = tmp_path/'source';root = tmp_path/'assembled';root.mkdir()
    if positions is None:
        positions = [dict(position_key='cf:one',evidence_kind='enter_pass_opportunity_cf',
            symbol='005930',item='005930',route='krx_only',entry_at=clock('09:00:30'),
            entry_reference_ask=100,entry_reference_role='native_entry_ask_price_path_only',
            automatic_management_allowed=True)]
    part = root/'part.json'
    part_sha = seal(part,dict(source_date=ISO_DAY,positions=positions,paths={}))
    partition_ref = storage.write_tree(root,[dict(path='part.json',artifact_sha256=part_sha)])
    population_ref = storage.write_tree(root,[p['position_key'] for p in positions])
    manifest = root/'manifest.json'
    seal(manifest,dict(schema='main_all_scope_exit_input_manifest_v2',source_date=ISO_DAY,
        target_date='2026-10-16',source_data_root=str(source),as_of=clock(),
        partitions_ref=partition_ref,population_ids_ref=population_ref))
    return source,root,manifest


def test_public_publish_read_excludes_forming_and_keeps_exact_item_and_source_bytes(tmp_path):
    path, receipt = publish(tmp_path,bars(11))
    before = diagnostic.carrier_generation(path)
    result,issue = diagnostic.series(tmp_path,DAY,'005930',as_of=clock())
    assert issue is None and len(result['bars']) == 10
    assert result['revision_sha256'] == receipt['shared_history_revision_sha256']
    assert result['bars'][-1][0] == clock('09:09:00')
    assert result['source_generation'] == before == diagnostic.carrier_generation(path)
    assert result['source_identity']['auth_scope'] == ['real','native-test']
    assert result['adjustment_equivalence_to_reference'] == 'unproven'
    assert diagnostic.series(tmp_path,DAY,'005930_NX',as_of=clock())[1] == 'minute_history_exact_item_or_known_revision_missing'


def test_wal_carrier_is_copied_without_source_sqlite_writes(tmp_path,monkeypatch):
    path,_ = publish(tmp_path,bars(2),now=clock('09:02:00'))
    with closing(sqlite3.connect(path)) as keeper:
        keeper.execute('SELECT count(*) FROM current').fetchone()
        _,receipt = publish(tmp_path,bars(10))
        before = diagnostic.carrier_generation(path)
        assert before['wal'] and before['wal']['size'] > 0
        originals = {p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in path.parent.iterdir()}
        read = history.read
        def private_read(root,*args,**kwargs):
            assert Path(root) != tmp_path
            return read(root,*args,**kwargs)
        monkeypatch.setattr(history,'read',private_read)
        result,issue = diagnostic.series(tmp_path,DAY,'005930',as_of=clock())
        assert issue is None and result['revision_sha256'] == receipt['shared_history_revision_sha256']
        assert result['source_generation'] == before
        assert {p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in path.parent.iterdir()} == originals


def test_public_publisher_transaction_can_overshoot_its_soft_cap_and_remain_readable(tmp_path,monkeypatch):
    path,_=publish(tmp_path,bars(10))
    # Scale the writer's cap to one byte above a real, already published DB.
    # The production transaction is unchanged and its insert crosses the cap.
    cap=path.stat().st_size+1
    monkeypatch.setattr(history,'MAX_DATABASE_BYTES',cap)
    _,receipt=publish(tmp_path,bars(400),now=clock('16:00:00'))
    assert path.stat().st_size>cap
    identity=history.key(('real','native-test'),'005930',DAY)
    native=history.read(tmp_path,identity,now=clock('16:00:00'),limit=400,
        include_forming=False,revision=receipt['shared_history_revision_sha256'])
    assert native is not None and len(native[0])==400
    before=diagnostic.carrier_generation(path)
    result,issue=diagnostic.series(tmp_path,DAY,'005930',as_of=clock('16:00:00'))
    assert issue is None and len(result['bars'])==400
    assert result['revision_sha256']==receipt['shared_history_revision_sha256']
    assert diagnostic.carrier_generation(path)==before
    assert history.publish(tmp_path,identity,bars(401),
        dict(api_id='ka10080',request_code='005930',rest_received_ts_ms=int(clock('16:01:00')*1000)),
        now=clock('16:01:00')) is False  # The next write is correctly denied.


def test_copy_resource_ceiling_is_combined_db_wal_and_checked_before_hashing(tmp_path,monkeypatch):
    path,_=publish(tmp_path,bars(2),now=clock('09:02:00'))
    with closing(sqlite3.connect(path)) as keeper:
        keeper.execute('SELECT count(*) FROM current').fetchone()
        publish(tmp_path,bars(10))
        db_size=path.stat().st_size;wal_size=Path(str(path)+'-wal').stat().st_size
        assert db_size>1 and wal_size>1
        cap=max(db_size,wal_size)+1
        assert db_size<=cap and wal_size<=cap and db_size+wal_size>cap
        monkeypatch.setattr(diagnostic,'MAX_COPY_CARRIER_BYTES',cap)
        monkeypatch.setattr(diagnostic,'byte_generation',lambda *a:pytest.fail('unadmitted carrier hashed'))
        result,issue=diagnostic.series(tmp_path,DAY,'005930',as_of=clock())
        assert result is None and issue=='minute_history_copy_resource_budget_exceeded'


def test_invalid_path_is_not_mislabeled_as_resource_exclusion(tmp_path):
    source=tmp_path/'source';path,_=publish(source,bars(10))
    linked=tmp_path/'linked';linked.symlink_to(source,target_is_directory=True)
    assert diagnostic.series(linked,DAY,'005930',as_of=clock())[1]=='minute_history_path_invalid'


@pytest.mark.parametrize('public_entry', ['series', 'build'])
def test_native_bar_payload_admitted_before_json_read_and_budget_is_not_source_gap(tmp_path,monkeypatch,public_entry):
    source,assembled,manifest=source_manifest(tmp_path)
    rows=bars(2)
    rows[0]['large_native_extra']='x'*(2*1024*1024)
    path,_=publish(source,rows,now=clock('09:02:00'))
    before=diagnostic.carrier_generation(path)
    monkeypatch.setattr(history,'read',lambda *a,**k:pytest.fail('unadmitted native JSON reader called'))
    with pytest.raises(ValueError,match='shared_research_budget_partition_resume_required'):
        if public_entry=='series':
            diagnostic.series(source,DAY,'005930',as_of=clock())
        else:
            diagnostic.build(manifest,input_root=assembled,data_root=source)
    assert diagnostic.carrier_generation(path)==before


def test_selected_native_payload_byte_count_uses_utf8_bytes_without_changing_bars(tmp_path):
    path,_=publish(tmp_path,bars(2),now=clock('09:02:00'))
    with closing(sqlite3.connect(path)) as db:
        for fingerprint,raw in db.execute('SELECT hash,content FROM bars').fetchall():
            db.execute('UPDATE bars SET content=? WHERE hash=?',
                (json.dumps(json.loads(raw),ensure_ascii=False),fingerprint))
        db.commit()
        expected=db.execute('SELECT sum(length(CAST(content AS BLOB))) FROM bars').fetchone()[0]
        chars=db.execute('SELECT sum(length(content)) FROM bars').fetchone()[0]
    assert expected>chars
    before=diagnostic.carrier_generation(path)
    source,issue=diagnostic.series(tmp_path,DAY,'005930',as_of=clock())
    assert issue is None and source['selected_bar_payload_bytes']==expected
    assert source['bar_decode_expansion_factor']==32 and len(source['bars'])==2
    assert diagnostic.carrier_generation(path)==before


def test_as_of_reads_available_historical_revision_behind_future_current(tmp_path):
    _,early = publish(tmp_path,bars(2),now=clock('09:02:00'))
    publish(tmp_path,bars(10))
    result,issue = diagnostic.series(tmp_path,DAY,'005930',as_of=clock('09:02:00'))
    assert issue is None and len(result['bars']) == 2
    assert result['revision_sha256'] == early['shared_history_revision_sha256']
    assert diagnostic.series(tmp_path,DAY,'005930',as_of=clock('09:01:59'))[0] is None


def test_native_multiday_prefix_is_verified_then_limited_to_diagnostic_day(tmp_path):
    previous = [{**bar,'source_timestamp':stamp} for bar,stamp in zip(bars(2),
        ('20261014152800','20261014152900'))]
    publish(tmp_path,previous+bars(10))
    result,issue=diagnostic.series(tmp_path,DAY,'005930',as_of=clock())
    assert issue is None and len(result['bars'])==10
    assert result['source_completed_bar_count']==12 and result['diagnostic_day_bar_count']==10
    assert result['bars'][0][0]==clock('09:00:00')


def test_multiple_auth_scopes_never_select_a_convenient_history(tmp_path):
    publish(tmp_path,bars(10))
    publish(tmp_path,bars(10),scope=('demo','other'))
    assert diagnostic.series(tmp_path,DAY,'005930',as_of=clock())[1] == 'minute_history_exact_scope_ambiguous'


def test_acquisition_sessions_share_chart_identity_and_select_latest_available_revision(tmp_path):
    publish(tmp_path,bars(2),now=clock('09:02:00'),session='krx_like_premarket')
    _,regular=publish(tmp_path,bars(5),now=clock('09:05:00'),session='KRX_REGULAR')
    _,closed=publish(tmp_path,bars(10),session='CLOSED')
    latest,issue=diagnostic.series(tmp_path,DAY,'005930',as_of=clock())
    assert issue is None and latest['revision_sha256']==closed['shared_history_revision_sha256']
    assert latest['source_identity']['session']=='CLOSED' and len(latest['bars'])==10
    assert latest['eligible_acquisition_sessions']==['CLOSED','KRX_REGULAR','krx_like_premarket']
    earlier,issue=diagnostic.series(tmp_path,DAY,'005930',as_of=clock('09:06:00'))
    assert issue is None and earlier['revision_sha256']==regular['shared_history_revision_sha256']
    assert earlier['source_identity']['session']=='KRX_REGULAR' and len(earlier['bars'])==5
    assert earlier['eligible_acquisition_sessions']==['KRX_REGULAR','krx_like_premarket']


def test_session_equivalence_never_crosses_authentication_scope(tmp_path):
    publish(tmp_path,bars(5),now=clock('09:05:00'),session='KRX_REGULAR')
    publish(tmp_path,bars(10),scope=('real','different-token-scope'),session='CLOSED')
    assert diagnostic.series(tmp_path,DAY,'005930',as_of=clock())[1]=='minute_history_exact_scope_ambiguous'


@pytest.mark.parametrize('conflicting', [False,True])
def test_equal_available_session_revisions_require_identical_bar_content(tmp_path,conflicting):
    _,one=publish(tmp_path,bars(10),session='KRX_REGULAR')
    _,two=publish(tmp_path,bars(10,high=106 if conflicting else 105),session='CLOSED')
    result,issue=diagnostic.series(tmp_path,DAY,'005930',as_of=clock())
    if conflicting:
        assert result is None and issue=='minute_history_same_clock_revision_conflict'
    else:
        assert issue is None and len(result['bars'])==10
        assert result['revision_sha256']==max(one['shared_history_revision_sha256'],two['shared_history_revision_sha256'])


def test_chart_producer_session_is_cache_identity_not_request_filter():
    """Inspect the real producer without importing its provider/authentication code."""
    import ast
    source=Path(__file__).resolve().parents[1]/'utils/kiwoom_utils.py'
    module=ast.parse(source.read_text())
    function=next(node for node in module.body if isinstance(node,ast.FunctionDef)
        and node.name=='get_minute_candles_ka10080_with_meta')
    assignment={node.targets[0].id:node.value for node in ast.walk(function)
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)}
    payload=assignment['payload']
    assert isinstance(payload,ast.Dict)
    assert [ast.literal_eval(key) for key in payload.keys]==['stk_cd','tic_scope','upd_stkpc_tp','base_dt']
    assert ast.unparse(assignment['history_key'].args[-1]).endswith('.session_regime')


def test_newer_revision_resolves_old_same_clock_conflict_but_cutoff_does_not(tmp_path):
    publish(tmp_path,bars(5),now=clock('09:05:00'),session='KRX_REGULAR')
    publish(tmp_path,bars(5,high=106),now=clock('09:05:00'),session='KRX_REGULAR')
    assert diagnostic.series(tmp_path,DAY,'005930',as_of=clock('09:06:00'))[1]=='minute_history_same_clock_revision_conflict'
    _,newer=publish(tmp_path,bars(10),session='CLOSED')
    result,issue=diagnostic.series(tmp_path,DAY,'005930',as_of=clock())
    assert issue is None and result['revision_sha256']==newer['shared_history_revision_sha256']
    assert diagnostic.series(tmp_path,DAY,'005930',as_of=clock('09:06:00'))[1]=='minute_history_same_clock_revision_conflict'


def test_all_same_clock_corrections_are_checked_even_below_equal_top_hashes(tmp_path):
    path=None
    for index in (0,1,10,3):
        path,_=publish(tmp_path,bars(10,high=105+index%2),session='KRX_REGULAR',receipt_tag=index)
    with closing(sqlite3.connect(path)) as db:
        manifests=[history._unpack(row[0]) for row in db.execute('SELECT manifest FROM revisions ORDER BY hash DESC')]
    assert len(manifests)==4
    assert manifests[0]['bar_hashes']==manifests[1]['bar_hashes']
    assert len({tuple(row['bar_hashes']) for row in manifests})==2
    assert diagnostic.series(tmp_path,DAY,'005930',as_of=clock())[1]=='minute_history_same_clock_revision_conflict'


def test_public_reader_rejects_corrupt_bar_and_invalid_manifest(tmp_path):
    path,_ = publish(tmp_path,bars(10))
    with closing(sqlite3.connect(path)) as db, db:
        db.execute("UPDATE bars SET content=? WHERE hash=(SELECT hash FROM bars LIMIT 1)",(b'{}',))
    result,issue = diagnostic.series(tmp_path,DAY,'005930',as_of=clock())
    assert result is None and issue == 'minute_history_native_reader_rejected'
    with closing(sqlite3.connect(path)) as db, db:
        db.execute('UPDATE revisions SET manifest=?',(b'not-zlib',))
    assert diagnostic.series(tmp_path,DAY,'005930',as_of=clock())[1] == 'minute_history_source_contract_invalid'


def test_wal_mutation_during_private_read_is_detected(tmp_path,monkeypatch):
    path,_ = publish(tmp_path,bars(2),now=clock('09:02:00'))
    with closing(sqlite3.connect(path)) as keeper:
        keeper.execute('SELECT count(*) FROM current').fetchone()
        publish(tmp_path,bars(10))
        before = diagnostic.carrier_generation(path)
        read = history.read
        def changed(*args,**kwargs):
            result = read(*args,**kwargs)
            publish(tmp_path,bars(11),now=clock('09:11:00'))
            return result
        monkeypatch.setattr(history,'read',changed)
        result,issue = diagnostic.series(tmp_path,DAY,'005930',as_of=clock())
        after = diagnostic.carrier_generation(path)
        assert before['database'] == after['database'] and before['wal'] != after['wal']
        assert result is None and issue == 'minute_history_provenance_changed'


def test_partial_entry_horizons_exclude_entry_bar_and_never_claim_intrabar_order():
    rows = [(clock('09:00:00'),1,999),(clock('09:01:00'),98,105),(clock('09:02:00'),97,106)]
    short = diagnostic.measure(100,clock('09:00:30'),rows,horizon_minutes=1)
    assert short['expected_completed_bars'] == 0 and short['net_high_bound_pct'] is None
    result = diagnostic.measure(100,clock('09:00:30'),rows,horizon_minutes=3)
    assert result['expected_completed_bars'] == result['observed_completed_bars'] == 2
    assert result['leading_unobserved_seconds'] == result['trailing_unobserved_seconds'] == 30
    assert result['horizon_fully_observed'] is False and result['intrabar_order_known'] is False
    assert result['net_high_bound_pct'] == pytest.approx(100*(106*.9977/100-1))
    gap = diagnostic.measure(100,clock('09:00:00'),rows[:1],horizon_minutes=3)
    assert gap['missing_completed_bar_count'] == 2 and not gap['horizon_fully_observed']


def test_build_preserves_denominators_code_sha_and_missing_ask(tmp_path):
    base = dict(symbol='005930',item='005930',route='krx_only',entry_at=clock('09:00:30'),
        evidence_kind='enter_pass_opportunity_cf',entry_reference_ask=100,
        entry_reference_role='native_entry_ask_price_path_only')
    positions = [dict(base,position_key='cf:valid'),dict(base,position_key='cf:missing',entry_reference_ask=None),
        dict(base,position_key='alternative:one',evidence_kind='actual_entry_alternative_exit')]
    source,root,manifest = source_manifest(tmp_path,positions)
    publish(source,bars(10))
    result = diagnostic.build(manifest,input_root=root,data_root=source)
    assert result['input_population_count'] == 3 and result['population_count'] == 2
    assert result['excluded_alternative_exit_count'] == 1
    by_id = {r['identity']:r for r in result['rows']}
    assert by_id['cf:valid']['status'] == 'price_path_diagnostic'
    assert by_id['cf:missing']['status'] == 'source_gap'
    assert result['diagnostic_code_sha256'] == byte_generation(Path(diagnostic.__file__))['sha256']
    assert not result['actual_profit_verified'] and not result['allowed_runtime_apply']
    assert result['model']['adjustment_equivalence_to_reference'] == 'unproven'


@pytest.mark.parametrize('fault',['census','duplicate','partition_hash','source_date','symbol'])
def test_manifest_identity_generation_and_symbol_are_verified(tmp_path,fault):
    source,root,manifest = source_manifest(tmp_path)
    value = json.loads(manifest.read_text());part_path=root/'part.json';part=json.loads(part_path.read_text())
    if fault == 'census':
        value['population_ids_ref'] = storage.write_tree(root,['another'])
    elif fault == 'partition_hash':
        part['positions'][0]['entry_reference_ask'] = 999
        part_path.write_text(json.dumps(part))
    else:
        if fault == 'duplicate':part['positions'].append(part['positions'][0])
        elif fault == 'source_date':part['source_date']='2026-10-14'
        elif fault == 'symbol':part['positions'][0]['symbol']='000660'
        part.pop('artifact_sha256');sha=seal(part_path,part)
        value['partitions_ref']=storage.write_tree(root,[dict(path='part.json',artifact_sha256=sha)])
    value.pop('artifact_sha256');seal(manifest,value)
    if fault == 'symbol':
        assert diagnostic.build(manifest,input_root=root,data_root=source)['rows'][0]['status']=='source_gap'
    else:
        with pytest.raises(ValueError):diagnostic.build(manifest,input_root=root,data_root=source)


def test_partition_mutation_during_history_read_is_rejected(tmp_path,monkeypatch):
    source,root,manifest = source_manifest(tmp_path);publish(source,bars(10))
    read=history.read
    def changed(*args,**kwargs):
        result=read(*args,**kwargs)
        with (root/'part.json').open('a') as handle:handle.write(' ')
        return result
    monkeypatch.setattr(history,'read',changed)
    with pytest.raises(ValueError,match='minute_diagnostic_partition_changed'):
        diagnostic.build(manifest,input_root=root,data_root=source)


def test_build_copies_daily_carrier_once_for_multiple_groups(tmp_path,monkeypatch):
    source,root,manifest=source_manifest(tmp_path)
    value=json.loads(manifest.read_text());part=json.loads((root/'part.json').read_text())
    part['positions'].append({**part['positions'][0],'position_key':'cf:other','symbol':'000660','item':'000660'})
    part.pop('artifact_sha256');sha=seal(root/'part.json',part)
    value['partitions_ref']=storage.write_tree(root,[dict(path='part.json',artifact_sha256=sha)])
    value['population_ids_ref']=storage.write_tree(root,['cf:one','cf:other'])
    value.pop('artifact_sha256');seal(manifest,value)
    publish(source,bars(10));publish(source,bars(10),item='000660')
    snapshot=diagnostic._snapshot;calls=[]
    def counted(*args,**kwargs):calls.append(args[1]);return snapshot(*args,**kwargs)
    monkeypatch.setattr(diagnostic,'_snapshot',counted)
    result=diagnostic.build(manifest,input_root=root,data_root=source)
    assert calls==[DAY] and len(result['source_revisions'])==2
