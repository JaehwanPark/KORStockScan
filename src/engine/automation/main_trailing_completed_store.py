"""Native completed-source producer and bounded immutable tree consumer.

The snapshot census owner publishes resident rows. Explicit offline preparation
enrolls original sealed projections through the existing streaming reader.
Normal research reads normalized objects only; neither path grants policy,
cost/custody, provider or order authority.
"""
import hashlib
import json
from pathlib import Path

from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.research_json_stream import resident_completed_rows
from src.engine.scalping.pre_submit_delay_initial_policy import _atomic,digest

SCHEMA='main_trailing_completed_source_index_v1'


def _record_rows(output,rows):
    for trade,quotes in rows:
        fields=storage.write_tree(output,({'key':key,'value':value} for key,value in trade.items()))
        vote=trade.get('holding_vote_source') or {}
        if not isinstance(vote,dict):vote={}
        yield dict(record_id=str(trade.get('id') or trade.get('record_id') or ''),
            fields_ref=fields,quotes_ref=quotes,vote_store_name=vote.get('store_name'))


def publish(data_root,sidecar,payload,*,projection_generation):
    from src.engine.sniper_trade_review_report import verify_completed_census_manifest
    root=Path(data_root).resolve();sidecar=Path(sidecar).resolve()
    day=payload['date']
    if (sidecar.parent!=root/'report/monitor_snapshots'
            or sidecar.name!=f'trade_review_{day}.completed_projection.json'
            or verify_completed_census_manifest(payload,day) is not None):
        raise ValueError('trailing_completed_index_producer_binding_invalid')
    rows=payload['sections']['completed_trade_projection']
    output=root/'report/main_trailing_completed_source'/day
    from src.engine.lifecycle.research_disk_budget import use
    with use(output),storage.compact_trees():
        reference=storage.write_tree(output,_record_rows(output,resident_completed_rows(rows,output)))
    if reference['count']!=len(rows):
        raise ValueError('trailing_completed_index_census_changed')
    body=dict(schema=SCHEMA,source_date=day,source_data_root=str(root),
        projection_generation=projection_generation,snapshot_identity=payload['snapshot_identity'],
        census_sha256=digest(payload['meta']['completed_census_manifest']),
        actual_cost_source_generation=payload['meta'].get('actual_cost_source_generation'),
        completed_count=len(rows),records_ref=reference,
        extraction_schema='native_resident_completed_rows_v1',
        vote_inventory_schema='completed_position_vote_store_names_v1',
        producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        runtime_effect=False,allowed_runtime_apply=False,semantic_verdict_reused=False)
    body['artifact_sha256']=digest(body)
    target=output/'generations'/(body['artifact_sha256']+'.json')
    if target.exists():
        if json.loads(target.read_bytes())!=body:
            raise ValueError('trailing_completed_index_generation_collision')
    else:
        _atomic(target,body)
    raw=target.read_bytes()
    return dict(schema=SCHEMA,manifest_path=str(target),
        manifest_generation=dict(path=target.name,size=len(raw),sha256=hashlib.sha256(raw).hexdigest()),
        artifact_sha256=body['artifact_sha256'])


def _offline_code():
    from src.engine.lifecycle import research_json_stream,holding_window_generation,snapshot_archive
    from src.engine.scalping import holding_path_vote_replay
    return digest({module.__name__:hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
        for module in (research_json_stream,storage,holding_window_generation,snapshot_archive,holding_path_vote_replay)}
        | {__name__:hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})


def _offline_epochs(root,day,dependency):
    from src.engine.lifecycle.snapshot_archive import _regular,archived_receipt
    directory=root/'report/monitor_snapshots'
    raw=directory/f'trade_review_{day}.json';sidecar=raw.with_suffix('.completed_projection.json')
    paths={Path(str(p)+'.dependencies.json') for p in (raw,sidecar)}
    paths.add(root/'report/strategy_position_fact_sync'/f'strategy_position_fact_sync_{day}.status.json')
    paths.update((root/'report/strategy_position_fact_sync/legacy_sources'/day).glob('*.json'))
    original=dependency.get('original_snapshot_manifest') or {}
    if original.get('path'):paths.add(Path(original['path']))
    result={}
    for path in sorted(paths):
        if not path.is_absolute() or '..'in path.parts or not path.is_relative_to(root):
            raise ValueError('trailing_completed_offline_source_path_invalid')
        result[str(path)]=_regular(path) if path.exists() or path.is_symlink() else None
    for path in (raw,sidecar):
        if path.exists() or path.is_symlink():result[str(path)]=_regular(path)
        elif Path(str(path)+'.gz').is_file():
            # A native lossless archive preserves the original source epoch.
            # Its current packed SHA/epoch is independently checked here.
            result[str(path)]=archived_receipt(path)['original_identity']
        else:result[str(path)]=None
    return result


def _offline_logical_sources(root,day,body,epochs):
    from src.engine.lifecycle.holding_window_generation import byte_generation
    raw=root/'report/monitor_snapshots'/f'trade_review_{day}.json'
    paths=(raw,raw.with_suffix('.completed_projection.json'))
    expected=body.get('offline_logical_generations')
    names={str(path)for path in paths if epochs[str(path)] is not None}
    if not isinstance(expected,dict) or set(expected)!=names:
        raise ValueError('trailing_completed_offline_logical_binding_invalid')
    for path in paths:
        if str(path) not in names:continue
        value=expected[str(path)]
        if (not isinstance(value,dict) or value.get('path')!=path.name
                or type(value.get('size')) is not int or value['size']<0
                or not isinstance(value.get('sha256'),str) or len(value['sha256'])!=64):
            raise ValueError('trailing_completed_offline_logical_binding_invalid')
        if not path.exists() and byte_generation(path)!=value:
            raise ValueError('trailing_completed_offline_logical_source_changed')


def _metadata(path):
    from .main_trailing_all_scope_research import _sealed
    from src.engine.lifecycle.snapshot_archive import _regular
    before=_regular(path)
    if before['size']>1024*1024:raise ValueError('trailing_completed_metadata_budget_exceeded')
    body=_sealed(path)
    if _regular(path)!=before:raise ValueError('trailing_completed_offline_source_changed')
    return body


def _offline_key(dependency,generation,epochs,code):
    # Observed later costs are independently validated by the caller. This
    # cache projects the immutable original rows, never a new money verdict.
    source={k:v for k,v in dependency.items() if k!='observed_actual_cost_source_generation'}
    return digest(dict(dependency=source,projection=generation,sources=epochs,code=code))


def _manifest_binding(path,body):
    raw=path.read_bytes()
    return dict(schema=SCHEMA,manifest_path=str(path),
        manifest_generation=dict(path=path.name,size=len(raw),sha256=hashlib.sha256(raw).hexdigest()),
        artifact_sha256=body['artifact_sha256'])


def offline_binding(data_root,day,*,dependency=None,projection_generation=None):
    """Small original-source cache lookup; never enroll or decode a source."""
    from datetime import date
    if date.fromisoformat(day).isoformat()!=day:raise ValueError('trailing_completed_source_date_invalid')
    root=Path(data_root).resolve();directory=root/'report/main_trailing_completed_source'/day/'generations'
    if not directory.exists() and not directory.is_symlink():return None,None
    code=_offline_code()
    if dependency is not None:
        epochs=_offline_epochs(root,day,dependency)
        key=_offline_key(dependency,projection_generation,epochs,code)
        paths=[directory/('offline-'+code+'-'+key+'.json')]
    else:
        paths=sorted(directory.glob('offline-'+code+'-*.json'))
        if len(paths)>64:raise ValueError('trailing_completed_offline_inventory_unbounded')
    found=[]
    for path in paths:
        if not path.exists() and not path.is_symlink():continue
        from src.engine.lifecycle.snapshot_archive import _regular
        before=_regular(path)
        if before['size']>1024*1024:raise ValueError('trailing_completed_metadata_budget_exceeded')
        body=_metadata(path)
        if (body.get('schema')!=SCHEMA or body.get('source_date')!=day
                or body.get('source_data_root')!=str(root) or body.get('runtime_effect') is not False
                or body.get('allowed_runtime_apply') is not False
                or body.get('extraction_schema')!='original_sealed_completed_stream_v1'
                or body.get('original_stream_consumed_to_eof') is not True):
            raise ValueError('trailing_completed_offline_manifest_invalid')
        if body.get('offline_code_sha256')!=code:continue
        original=body.get('original_dependency')
        if not isinstance(original,dict):raise ValueError('trailing_completed_offline_manifest_invalid')
        current=_offline_epochs(root,day,original)
        if current!=body.get('offline_source_epochs'):continue
        _offline_logical_sources(root,day,body,current)
        expected=_offline_key(original,body.get('projection_generation'),current,code)
        if path.name!='offline-'+code+'-'+expected+'.json':raise ValueError('trailing_completed_offline_manifest_invalid')
        if dependency is not None and expected!=key:raise ValueError('trailing_completed_offline_source_changed')
        if _regular(path)!=before:raise ValueError('trailing_completed_offline_source_changed')
        found.append((_manifest_binding(path,body),body))
    if len(found)>1:raise ValueError('trailing_completed_offline_generation_conflict')
    return found[0] if found else (None,None)


def binding(data_root,dependency,*,projection_generation=None):
    native=dependency.get('trailing_completed_index')
    if native:return native
    return offline_binding(data_root,dependency['date'],dependency=dependency,
        projection_generation=projection_generation or dependency.get('projection'))[0]


def admit_window(data_root,day,*,start_date=None):
    """Admit byte hashes from the verified producer; never a semantic verdict."""
    from datetime import date,timedelta
    from src.engine.infrastructure.validation_digest_session import ACTIVE
    from .main_trailing_source_store import DEFAULT_START_DATE
    session=ACTIVE.get()
    if session is None or session.binding['role']!='postclose':return 0
    root=Path(data_root).resolve()
    if session.data_root.resolve()!=root or session.binding['day']!=day:
        raise ValueError('trailing_completed_digest_owner_mismatch')
    cursor=date.fromisoformat(start_date or DEFAULT_START_DATE);end=date.fromisoformat(day);count=0
    while cursor<=end:
        _,body=offline_binding(root,cursor.isoformat())
        if body:
            for name,generation in body['offline_logical_generations'].items():
                path=Path(name)
                if not path.is_file():continue  # Native archiver owns the gzip proof.
                identity=body['offline_source_epochs'][name]
                session.admit_native_generation(path,generation,[identity[k]for k in
                    ('device','inode','size','mtime_ns','ctime_ns')],proof_sha256=body['artifact_sha256'])
                count+=1
        cursor+=timedelta(days=1)
    return count


def prepare_window(data_root,days):
    """Explicit offline predecessor for native and retained original cohorts."""
    from src.engine.lifecycle.holding_window_generation import capture_window,byte_generation,verified_legacy_projection_dependency
    from src.engine.lifecycle.snapshot_archive import present,snapshot_identity_matches
    from src.engine.lifecycle.research_json_stream import completed_rows
    from src.engine.lifecycle.research_disk_budget import use
    from src.engine.infrastructure.validation_digest_session import postclose_session
    root=Path(data_root).resolve();directory=root/'report/monitor_snapshots';pending=[];result=[]
    for day in days:
        raw=directory/f'trade_review_{day}.json'
        if not present(raw):continue
        sidecar=raw.with_suffix('.completed_projection.json')
        if not present(sidecar):sidecar=raw
        receipt_path=Path(str(sidecar)+'.dependencies.json')
        native=_metadata(receipt_path) if receipt_path.is_file() or receipt_path.is_symlink() else None
        if native and native.get('trailing_completed_index'):
            result.append(dict(path=str(sidecar),status='native_index_present'));continue
        cached,_=offline_binding(root,day)
        if cached:result.append(dict(path=str(sidecar),status='offline_index_ready',generation=cached));continue
        pending.append(day)
    if not pending:return result
    # The same full native window contract chooses identifiable exclusions as
    # the holding consumer. An unverified historical date never becomes empty.
    with postclose_session(root,days[-1]):
        window=capture_window(root,days,allow_cost_revision=True)
        for day in pending:
            window_day=window['dependencies'][day]
            if window_day['status'] not in {'observed','valid_empty'}:
                result.append(dict(path=str(directory/f'trade_review_{day}.json'),status='source_gap',
                    reason=window_day.get('reason') or window_day['status']));continue
            raw=directory/f'trade_review_{day}.json';sidecar=raw.with_suffix('.completed_projection.json')
            if not present(sidecar):sidecar=raw
            generation=byte_generation(sidecar);receipt_path=Path(str(sidecar)+'.dependencies.json')
            if receipt_path.is_file():
                dependency=_metadata(receipt_path)
                if (dependency.get('schema')!='holding_projection_dependency_receipt_v1'
                        or dependency.get('date')!=day or dependency.get('projection')!=generation
                        or dependency.get('meta',{}).get('snapshot_profile')!='postclose_exit'
                        or not dependency.get('census_sha256')
                        or not snapshot_identity_matches(raw,dependency.get('snapshot_identity'))):
                    raise ValueError('trailing_completed_offline_native_binding_invalid')
            else:
                dependency,_=verified_legacy_projection_dependency(root,day,projection_generation=generation)
            epochs=_offline_epochs(root,day,dependency);code=_offline_code()
            logical_generations={str(path):byte_generation(path)for path in
                (raw,raw.with_suffix('.completed_projection.json'))if present(path)}
            output=root/'report/main_trailing_completed_source'/day
            with use(output),storage.compact_trees():
                reference=storage.write_tree(output,_record_rows(output,completed_rows(sidecar,output,expected_generation=generation)))
            if (reference['count']!=dependency['completed_count']
                    or epochs!=_offline_epochs(root,day,dependency) or byte_generation(sidecar)!=generation
                    or code!=_offline_code()):
                raise ValueError('trailing_completed_offline_source_changed')
            body=dict(schema=SCHEMA,source_date=day,source_data_root=str(root),projection_generation=generation,
                snapshot_identity=dependency['snapshot_identity'],census_sha256=dependency['census_sha256'],
                actual_cost_source_generation=dependency['meta'].get('actual_cost_source_generation'),
                completed_count=reference['count'],records_ref=reference,
                extraction_schema='original_sealed_completed_stream_v1',vote_inventory_schema='completed_position_vote_store_names_v1',
                original_dependency=dependency,offline_source_epochs=epochs,offline_code_sha256=code,
                offline_logical_generations=logical_generations,
                original_stream_consumed_to_eof=True,
                runtime_effect=False,allowed_runtime_apply=False,semantic_verdict_reused=False)
            body['artifact_sha256']=digest(body)
            if len(storage.encoded(body))>1024*1024:raise ValueError('trailing_completed_metadata_budget_exceeded')
            target=output/'generations'/('offline-'+code+'-'+_offline_key(dependency,generation,epochs,code)+'.json')
            if target.exists():
                if _metadata(target)!=body:raise ValueError('trailing_completed_index_generation_collision')
            else:_atomic(target,body)
            result.append(dict(path=str(sidecar),status='offline_index_prepared',generation=_manifest_binding(target,body)))
    return result


def vote_store_names(data_root,days):
    """Cohort metadata only; legacy cohorts retain their bounded intake path."""
    import re
    from .main_trailing_all_scope_research import _sealed
    from src.engine.lifecycle.holding_window_generation import byte_generation
    root=Path(data_root).resolve();names=set();native_days=0
    for day in days:
        sidecar=root/'report/monitor_snapshots'/f'trade_review_{day}.completed_projection.json'
        receipt=Path(str(sidecar)+'.dependencies.json')
        if not receipt.is_file():
            if any(p.is_file() for p in (sidecar,Path(str(sidecar)+'.gz'),
                sidecar.with_name(f'trade_review_{day}.json'),sidecar.with_name(f'trade_review_{day}.json.gz'))):
                migrated,body=offline_binding(root,day)
                if migrated:
                    native_days+=1
                    allowed=root/'report/main_trailing_completed_source'/day
                    count=0
                    for row in storage.iter_tree(allowed,body['records_ref']):
                        name=row.get('vote_store_name');count+=1
                        if name is not None:
                            if not isinstance(name,str) or re.fullmatch(r'[0-9a-f]{64}\.jsonl',name) is None:
                                raise ValueError('trailing_completed_vote_store_name_invalid')
                            names.add(name)
                    if count!=body['completed_count'] or offline_binding(root,day)[0]!=migrated:
                        raise ValueError('trailing_completed_index_census_changed')
                    continue
                return None
            continue
        if receipt.stat().st_size>1024*1024:raise ValueError('trailing_completed_metadata_budget_exceeded')
        dependency=_sealed(receipt);bound=binding(root,dependency)
        if not bound:return None
        path=Path(bound.get('manifest_path','')).resolve()
        allowed=root/'report/main_trailing_completed_source'/day
        if (bound.get('schema')!=SCHEMA or not path.is_relative_to(allowed/'generations')
                or path.stat().st_size>1024*1024 or byte_generation(path)!=bound.get('manifest_generation')):
            raise ValueError('trailing_completed_index_manifest_changed')
        body=_sealed(path)
        if (body.get('schema')!=SCHEMA or body.get('source_date')!=day
                or body.get('source_data_root')!=str(root)
                or body.get('artifact_sha256')!=bound.get('artifact_sha256')
                or body.get('projection_generation')!=dependency.get('projection')):
            raise ValueError('trailing_completed_index_source_binding_invalid')
        if body.get('vote_inventory_schema')!='completed_position_vote_store_names_v1':return None
        native_days+=1
        count=0
        for row in storage.iter_tree(allowed,body['records_ref']):
            name=row.get('vote_store_name');count+=1
            if name is not None:
                if not isinstance(name,str) or re.fullmatch(r'[0-9a-f]{64}\.jsonl',name) is None:
                    raise ValueError('trailing_completed_vote_store_name_invalid')
                names.add(name)
        if count!=body['completed_count']:raise ValueError('trailing_completed_index_census_changed')
    return names if native_days else None


def read(data_root,dependency,output_root,*,projection_generation=None):
    """Verify and copy only the referenced normalized chunks."""
    from .main_trailing_all_scope_research import _sealed
    from src.engine.lifecycle.holding_window_generation import byte_generation
    root=Path(data_root).resolve();bound=binding(root,dependency,projection_generation=projection_generation) or {}
    path=Path(bound.get('manifest_path','')).resolve()
    allowed=root/'report/main_trailing_completed_source'/dependency['date']
    if (bound.get('schema')!=SCHEMA or not path.is_relative_to(allowed/'generations')
            or byte_generation(path)!=bound.get('manifest_generation')):
        raise ValueError('trailing_completed_index_manifest_changed')
    body=_sealed(path)
    if (body.get('schema')!=SCHEMA or body.get('source_date')!=dependency['date']
            or body.get('source_data_root')!=str(root)
            or body.get('artifact_sha256')!=bound.get('artifact_sha256')
            or body.get('projection_generation')!=(projection_generation or dependency['projection'])
            or body.get('snapshot_identity')!=dependency['snapshot_identity']
            or body.get('census_sha256')!=dependency['census_sha256']
            or body.get('actual_cost_source_generation')!=dependency['meta'].get('actual_cost_source_generation')
            or body.get('completed_count')!=dependency['completed_count']
            or body.get('runtime_effect') is not False or body.get('allowed_runtime_apply') is not False):
        raise ValueError('trailing_completed_index_source_binding_invalid')
    count=0
    for row in storage.iter_tree(allowed,body['records_ref']):
        fields={}
        for field in storage.iter_tree(allowed,row['fields_ref']):
            if field['key'] in fields:raise ValueError('trailing_completed_index_duplicate_field')
            value=field['value']
            if isinstance(value,dict) and value.get('schema')==storage.SCHEMA:
                storage.copy_tree(allowed,output_root,value)
            fields[field['key']]=value
        if str(fields.get('id') or fields.get('record_id') or '')!=row['record_id']:
            raise ValueError('trailing_completed_index_identity_changed')
        storage.copy_tree(allowed,output_root,row['quotes_ref']);count+=1
        yield fields,row['quotes_ref']
    if count!=body['completed_count'] or byte_generation(path)!=bound['manifest_generation']:
        raise ValueError('trailing_completed_index_census_changed')
    if path.name.startswith('offline-') and binding(root,dependency,projection_generation=projection_generation)!=bound:
        raise ValueError('trailing_completed_offline_source_changed')
