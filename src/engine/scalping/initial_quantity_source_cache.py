"""Byte-verified per-date quantity features; costs never own this cache.

Offline SCALPING research cache. A corrupted disposable cache is rebuilt from
verified raw sources. Pinned report evidence and raw sources are never deleted.
"""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import uuid
from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.research_input_budget import Claim, LIMIT_BYTES
from src.engine.lifecycle.holding_window_generation import byte_generation
from src.engine.scalping.pre_submit_delay_initial_policy import _atomic


class ResidentPaths(dict):
    """Keep the shared claim alive for the entire retained feature lifetime."""
    def __init__(self):
        super().__init__()
        self.claim=Claim(0)
        self.partitions=[]


class BoundedRows(list):
    def __init__(self, claim):
        super().__init__()
        self.claim=claim

    def append(self, value):
        self.claim.grow(len(storage.encoded(encode(value)))*8)
        super().append(value)


class ResidentFacts(BoundedRows):
    def __init__(self,rows,claim=None):
        super().__init__(claim if claim is not None else Claim(0))
        if claim is not None:
            list.extend(self,rows)
        else:
            for row in rows:self.append(row)


def encode(value):
    if isinstance(value,datetime):return {'__quantity_datetime__':value.isoformat()}
    if isinstance(value,dict):return {k:encode(v) for k,v in value.items()}
    if isinstance(value,list):return [encode(v) for v in value]
    return value


def decode(value):
    if isinstance(value,dict):
        if set(value)=={'__quantity_datetime__'}:return datetime.fromisoformat(value['__quantity_datetime__'])
        return {k:decode(v) for k,v in value.items()}
    if isinstance(value,list):return [decode(v) for v in value]
    return value


def fingerprint(trades,path,horizon):
    from src.engine.scalping.initial_quantity_policy import _quantity_capture_lifecycle_sources
    dates = {r['entry_date'] for r in trades}
    if len(dates) != 1:
        raise ValueError('quantity_capture_cache_date_invalid')
    captures, _ = _quantity_capture_lifecycle_sources(path.parents[1], next(iter(dates)))
    leaf=byte_generation(path) if path.exists() else None
    archive=Path(str(path)+'.archive_receipt.json')
    engine=Path(__file__).resolve().parents[1]
    readers={name:engine/'scalping'/name for name in (
        'initial_quantity_policy.py','initial_quantity_source_cache.py',
        'initial_quantity_cap_observation.py','initial_quantity_type.py')}
    readers['utils/jsonl_io.py']=engine.parent/'utils/jsonl_io.py'
    reader={name:hashlib.sha256(path.read_bytes()).hexdigest()
            for name,path in readers.items()}
    return dict(schema='initial_quantity_source_features_v4',source=leaf,
                archive=byte_generation(archive) if archive.exists() else None,
                capture_lifecycle_generation=captures,
                reader=reader, horizon=horizon,
                trades=[{k:r.get(k) for k in ('trade_id','record_id','stock_code','entry_date','exit_date','entry_at_fact_buy_time','exit_at')} for r in trades])


def _read_index(path):
    """Bound the read itself before decoding, including file growth races."""
    if path.is_symlink() or path.stat().st_size>storage.RECORD_BYTES:
        raise ValueError('cache_index_invalid')
    with path.open('rb') as handle:
        raw=handle.read(storage.RECORD_BYTES+1)
    if len(raw)>storage.RECORD_BYTES:
        raise ValueError('cache_index_invalid')
    value=json.loads(raw)
    if not isinstance(value,dict):raise ValueError('cache_index_invalid')
    return value


def join(trades, *, data_dir, scan_seconds=None, source_receipts=None, price_horizon_seconds=600):
    from src.engine.scalping.initial_quantity_policy import _digest, _join_post_fill_paths_uncached
    from src.utils.jsonl_io import existing_or_gzip_path
    from collections import defaultdict
    groups=defaultdict(list)
    for trade in trades:groups[trade['entry_date']].append(trade)
    result=ResidentPaths()
    for day,rows in sorted(groups.items()):
        raw=existing_or_gzip_path(Path(data_dir)/'pipeline_events'/f'pipeline_events_{day}.jsonl')
        before=fingerprint(rows,raw,price_horizon_seconds);key=_digest(before)
        base=Path(data_dir)/'report/initial_entry_quantity_type_policy/source_features'/day/key
        index=base/'index.json';cached=None
        if index.exists():
            try:
                value=_read_index(index)
                if value['manifest']!=before or value['sha256']!=_digest({k:v for k,v in value.items() if k!='sha256'}):raise ValueError('cache_changed')
                tree_root=Path(value.get('tree_root',base))
                if not tree_root.is_absolute() or not tree_root.resolve().is_relative_to(base.resolve()):raise ValueError('cache_root_invalid')
                payload=ResidentPaths();size=0
                for row in storage.iter_tree(tree_root,value['tree']):
                    size+=len(storage.encoded(row))*8
                    if size>LIMIT_BYTES:raise ValueError('shared_research_budget_partition_resume_required')
                    payload.claim.grow(len(storage.encoded(row))*8)
                    bucket=payload.setdefault(row['trade_id'],{})
                    if row['kind']=='scalar':bucket[row['field']]=decode(row['value'])
                    else:bucket.setdefault(row['field'],[]).append(decode(row['value']))
                if set(payload)!={r['trade_id'] for r in rows}:raise ValueError('cache_cohort_changed')
                cached=payload
                if source_receipts is not None:source_receipts.update(value['source_receipts'])
            except (OSError,ValueError,KeyError,TypeError) as exc:
                if 'budget' in str(exc):raise
                # A new disposable namespace avoids overwriting referenced shards.
                cached=None
                base=base/('repair-'+uuid.uuid4().hex)
        if cached is None:
            receipts={};timing={}
            cached=_join_post_fill_paths_uncached(rows,data_dir=data_dir,source_receipts=receipts,
                scan_seconds=timing,price_horizon_seconds=price_horizon_seconds)
            if fingerprint(rows,raw,price_horizon_seconds)!=before:raise ValueError('quantity_raw_generation_changed')
            def records():
                for tid,bucket in sorted(cached.items()):
                    for field,value in sorted(bucket.items()):
                        if isinstance(value,list):
                            # Empty arrays still carry their required field.
                            if not value:yield dict(trade_id=tid,kind='scalar',field=field,value=[])
                            for item in value:yield dict(trade_id=tid,kind='list',field=field,value=encode(item))
                        else:yield dict(trade_id=tid,kind='scalar',field=field,value=encode(value))
            tree=storage.write_tree(base,records())
            body=dict(manifest=before,tree=tree,tree_root=str(base.resolve()),source_receipts=receipts)
            _atomic(base/'index.json',{**body,'sha256':_digest(body)})
            if index!=base/'index.json':
                # Only this disposable lookup changes. The immutable repaired
                # shards and every published source/report remain untouched.
                _atomic(index,{**body,'sha256':_digest(body)})
            if source_receipts is not None:source_receipts.update(receipts)
            if scan_seconds is not None:scan_seconds.update(timing)
        # Cold lists already own an admitted claim. Warm decoded features are
        # admitted before they escape this partition into the retained result.
        result.partitions.append(cached)
        if fingerprint(rows,raw,price_horizon_seconds)!=before:raise ValueError('quantity_raw_generation_changed')
        result.update(cached)
    return result


def joint_records(trades, paths, rows, grid, *, data_dir, cost_rate):
    """Reuse execution-only partitions; actual-cost weights are reevaluated.

    Cached shards are disposable. The evaluator independently reconstructs
    execution outcomes once in its byte-verified validation context.
    """
    from src.engine.scalping.initial_quantity_policy import _digest
    from src.engine.scalping.initial_quantity_refresh_evaluation import execution_case
    readers=('initial_quantity_refresh_evaluation.py','initial_quantity_timeout_research.py','initial_quantity_policy.py','initial_quantity_cap_observation.py','initial_quantity_timeout.py','entry_split_order_plan.py')
    reader={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in readers}
    for trade in trades:
        tid=trade['trade_id'];row=rows[tid];path=paths.get(tid,{})
        model={k:trade[k] for k in ('buy_qty','buy_price','sell_price','exit_at')}
        model.update(quantity_type=row['quantity_type'],comparison_cost_rate=cost_rate)
        source=row.get('cap_source') or {}
        manifest=dict(model=model,path=encode(path),source=source,grid=grid,reader=reader)
        key=_digest(manifest)
        base=Path(data_dir)/'report/initial_entry_quantity_type_policy/execution_features'/trade['entry_date']/key
        index=base/'index.json';ref=None
        if index.is_file():
            try:
                value=_read_index(index)
                if value['input_sha256']!=key:raise ValueError('execution_cache_invalid')
                # Complete validation before yielding avoids mixed old/new rows
                # if a late leaf is corrupt.
                tree_root=Path(value.get('tree_root',base))
                if not tree_root.is_absolute() or not tree_root.resolve().is_relative_to(base.resolve()):raise ValueError('execution_cache_root_invalid')
                for _ in storage.iter_tree(tree_root,value['tree']):pass
                ref=value['tree']
            except (OSError,ValueError,KeyError,TypeError):
                base=base/('repair-'+uuid.uuid4().hex)
        if ref is None:
            ref=storage.write_tree(base,(
                dict(trade_id=tid,key=k,outcome=execution_case(model,path,source,mode=v['mode'],shape=v['shape'],horizon=v['horizon'],reserve=v['reserve']))
                for k,v in grid.items()))
            tree_root=base
            _atomic(base/'index.json',dict(input_sha256=key,tree=ref,tree_root=str(tree_root.resolve())))
            if index != base/'index.json':
                _atomic(index,dict(input_sha256=key,tree=ref,tree_root=str(tree_root.resolve())))
        yield from storage.iter_tree(tree_root,ref)
