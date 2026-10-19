"""Native completed-source producer and bounded immutable tree consumer.

The snapshot census owner publishes this while it still owns resident rows.
Research reads normalized objects only. This package does not read raw files,
select a policy, alter costs/custody, call a provider, or place orders.
"""
import hashlib
import json
from pathlib import Path

from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.research_json_stream import resident_completed_rows
from src.engine.scalping.pre_submit_delay_initial_policy import _atomic,digest

SCHEMA='main_trailing_completed_source_index_v1'


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
    def records():
        for trade,quotes in resident_completed_rows(rows,output):
            fields=storage.write_tree(output,({'key':key,'value':value} for key,value in trade.items()))
            vote=trade.get('holding_vote_source') or {}
            if not isinstance(vote,dict):vote={}
            yield dict(record_id=str(trade.get('id') or trade.get('record_id') or ''),
                fields_ref=fields,quotes_ref=quotes,
                vote_store_name=vote.get('store_name'))
    with use(output),storage.compact_trees():
        reference=storage.write_tree(output,records())
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
                    sidecar.with_name(f'trade_review_{day}.json'),sidecar.with_name(f'trade_review_{day}.json.gz'))):return None
            continue
        if receipt.stat().st_size>1024*1024:raise ValueError('trailing_completed_metadata_budget_exceeded')
        dependency=_sealed(receipt);binding=dependency.get('trailing_completed_index') or {}
        if not binding:return None
        path=Path(binding.get('manifest_path','')).resolve()
        allowed=root/'report/main_trailing_completed_source'/day
        if (binding.get('schema')!=SCHEMA or not path.is_relative_to(allowed/'generations')
                or path.stat().st_size>1024*1024 or byte_generation(path)!=binding.get('manifest_generation')):
            raise ValueError('trailing_completed_index_manifest_changed')
        body=_sealed(path)
        if (body.get('schema')!=SCHEMA or body.get('source_date')!=day
                or body.get('source_data_root')!=str(root)
                or body.get('artifact_sha256')!=binding.get('artifact_sha256')
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


def read(data_root,dependency,output_root):
    """Verify and copy only the referenced normalized chunks."""
    from .main_trailing_all_scope_research import _sealed
    from src.engine.lifecycle.holding_window_generation import byte_generation
    root=Path(data_root).resolve();binding=dependency.get('trailing_completed_index') or {}
    path=Path(binding.get('manifest_path','')).resolve()
    allowed=root/'report/main_trailing_completed_source'/dependency['date']
    if (binding.get('schema')!=SCHEMA or not path.is_relative_to(allowed/'generations')
            or byte_generation(path)!=binding.get('manifest_generation')):
        raise ValueError('trailing_completed_index_manifest_changed')
    body=_sealed(path)
    if (body.get('schema')!=SCHEMA or body.get('source_date')!=dependency['date']
            or body.get('source_data_root')!=str(root)
            or body.get('artifact_sha256')!=binding.get('artifact_sha256')
            or body.get('projection_generation')!=dependency['projection']
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
    if count!=body['completed_count'] or byte_generation(path)!=binding['manifest_generation']:
        raise ValueError('trailing_completed_index_census_changed')
