"""Byte-verified quantity features with pinned as-of terminal generations.

Offline SCALPING research cache. A corrupted disposable cache is rebuilt from
verified raw sources. Pinned report evidence and raw sources are never deleted.
"""
from datetime import datetime
import hashlib
import json
from pathlib import Path
from collections import OrderedDict
import uuid
from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.research_input_budget import Claim, LIMIT_BYTES
from src.engine.lifecycle.holding_window_generation import byte_generation
from src.engine.scalping.pre_submit_delay_initial_policy import _atomic


QUANTITY_FACT_STRATEGIES = ("SCALPING", "SCALP")
QUANTITY_FACT_CUSTODIES = ("SCANNER", "SCALP_BASE")
_VERIFIED_COMPLETION_CONTEXTS = OrderedDict()


def completion_fact_scope(row):
    """Existing Main quantity population, never additional custody authority."""
    return (str(row.get('strategy') or '').upper() in QUANTITY_FACT_STRATEGIES
            and str(row.get('position_tag') or '').upper() in QUANTITY_FACT_CUSTODIES)


def _copy_resident(value, memo=None):
    """Copy admitted data once, preserving shared owners within a deep copy."""
    from copy import copy, deepcopy
    result = type(value).__new__(type(value))
    base = dict if isinstance(value, dict) else list
    base.__init__(result)
    if memo is None:
        # A shallow copy shares payload references but owns its reservation.
        claim = copy(value.claim)
        try:
            result.__dict__.update(value.__dict__)
            result.claim = claim
            (dict.update if base is dict else list.extend)(result, value)
        except BaseException:
            result.__dict__.clear()
            base.clear(result)
            claim.close()
            raise
        return result
    previous = set(memo)
    memo[id(value)] = result
    try:
        # Claim.__deepcopy__ admits bytes before any row is duplicated. Memo
        # preserves shared list/partition owners without reacquiring twice.
        result.__dict__.update(deepcopy(value.__dict__, memo))
        if base is dict:
            for key, item in value.items():
                dict.__setitem__(result, deepcopy(key, memo), deepcopy(item, memo))
        else:
            # These rows are covered by the copied claim. BoundedRows.append
            # would charge the original reservation again during reconstruction.
            list.extend(result, (deepcopy(item, memo) for item in value))
    except BaseException:
        # Keep caller-owned memo entries and original claims untouched. A
        # failed clone may survive in an exception traceback or caller memo.
        for key in set(memo) - previous:
            copied = memo.pop(key)
            if isinstance(copied, Claim):
                copied.close()
        result.__dict__.clear()
        base.clear(result)
        raise
    return result


class ResidentPaths(dict):
    """Keep the shared claim alive for the entire retained feature lifetime."""
    def __init__(self):
        super().__init__()
        self.claim=Claim(0)
        self.partitions=[]

    def __copy__(self):
        return _copy_resident(self)

    def __deepcopy__(self, memo):
        return _copy_resident(self, memo)


class BoundedRows(list):
    def __init__(self, claim):
        super().__init__()
        self.claim=claim

    def append(self, value):
        self.claim.grow(len(storage.encoded(encode(value)))*8)
        super().append(value)

    def __copy__(self):
        return _copy_resident(self)

    def __deepcopy__(self, memo):
        return _copy_resident(self, memo)


class ResidentFacts(BoundedRows):
    def __init__(self,rows,claim=None):
        super().__init__(claim if claim is not None else Claim(0))
        if claim is not None:
            list.extend(self,rows)
        else:
            for row in rows:self.append(row)


def completion_generation_reference(generation):
    """New research generations have one shared native proof, not N copies."""
    costs = (generation.get('completion_snapshot_source') or {}).get('actual_cost_source_generation') or {}
    if 'quantity_research_cost_generation' not in costs:
        return generation
    return dict(schema='initial_quantity_completion_generation_reference_v1',
                source_date=generation['source_date'], generation_sha256=hashlib.sha256(storage.encoded(generation)).hexdigest())


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
    from src.engine.automation.main_trailing_source_store import generation
    leaf=(byte_generation(path) if path.stat().st_size<=4*1024*1024
          else generation(path.parents[1], path)) if path.exists() else None
    archive=Path(str(path)+'.archive_receipt.json')
    engine=Path(__file__).resolve().parents[1]
    readers={name:engine/'scalping'/name for name in (
        'initial_quantity_policy.py','initial_quantity_source_cache.py',
        'initial_quantity_cap_observation.py','initial_quantity_type.py')}
    readers['utils/jsonl_io.py']=engine.parent/'utils/jsonl_io.py'
    readers['trading/market/execution_venue.py']=engine.parent/'trading/market/execution_venue.py'
    readers['lifecycle/research_input_budget.py']=engine/'lifecycle/research_input_budget.py'
    readers['lifecycle/research_json_stream.py']=engine/'lifecycle/research_json_stream.py'
    readers['automation/main_trailing_source_store.py']=engine/'automation/main_trailing_source_store.py'
    reader={name:hashlib.sha256(path.read_bytes()).hexdigest()
            for name,path in readers.items()}
    legacy_fields = ('trade_id','record_id','stock_code','entry_date','exit_date',
                     'entry_at_fact_buy_time','exit_at','completion_generation','fact_generation')
    # Cost allocation is independently checked against the complete native
    # generations. Price-feature reuse depends on execution inputs, so a new
    # confirmed-cost observation must not decode the same raw price partition.
    execution_fields = ('trade_id','record_id','stock_code','entry_date','exit_date',
                        'entry_at_fact_buy_time','exit_at','buy_qty','buy_price','sell_price')
    allocated = any(r.get('cost_basis') == 'broker_confirmed_total_allocated' for r in trades)
    from src.engine.lifecycle.holding_window_generation import source_stat
    return dict(schema='initial_quantity_source_features_v6' if allocated else 'initial_quantity_source_features_v5',source=leaf,
                physical_source_stat=list(source_stat(path.stat())) if path.exists() else None,
                archive=byte_generation(archive) if archive.exists() else None,
                capture_lifecycle_generation=captures,
                reader=reader, horizon=horizon,
                trades=[{k:r.get(k) for k in (execution_fields if r.get('cost_basis') == 'broker_confirmed_total_allocated' else legacy_fields)} for r in trades])


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
            receipts={};timing={};byte_proofs={}
            cached=_join_post_fill_paths_uncached(rows,data_dir=data_dir,source_receipts=receipts,
                scan_seconds=timing,price_horizon_seconds=price_horizon_seconds,
                source_byte_proofs=byte_proofs)
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
            body=dict(manifest=before,tree=tree,tree_root=str(base.resolve()),source_receipts=receipts,
                      source_byte_proofs=byte_proofs)
            _atomic(base/'index.json',{**body,'sha256':_digest(body)})
            if index!=base/'index.json':
                # Only this disposable lookup changes. The immutable repaired
                # shards and every published source/report remain untouched.
                _atomic(index,{**body,'sha256':_digest(body)})
            if source_receipts is not None:source_receipts.update(receipts)
            if scan_seconds is not None:scan_seconds.update(timing)
            value={**body,'sha256':_digest(body)}
        # Cold lists already own an admitted claim. Warm decoded features are
        # admitted before they escape this partition into the retained result.
        result.partitions.append(cached)
        if fingerprint(rows,raw,price_horizon_seconds)!=before:raise ValueError('quantity_raw_generation_changed')
        # Reuse only the full byte hash produced in this exact native epoch;
        # every semantic validator still executes against the current readers.
        from src.engine.infrastructure.validation_digest_session import ACTIVE
        active=ACTIVE.get()
        proof=value.get('source_byte_proofs',{}).get(day)
        if active is not None and proof is not None and before.get('source',{}).get('source_stat'):
            observed=before['physical_source_stat']
            if (active.binding['role']!='postclose' or list(proof['source_stat'])!=list(observed)
                    or proof['generation']['path']!=raw.name
                    or proof['generation']['size']!=observed[2]):
                raise ValueError('quantity_feature_byte_proof_unbound')
            active.admit_native_generation(raw,proof['generation'],observed,
                                           proof_sha256=value['sha256'])
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
    reader['trading/market/execution_venue.py']=hashlib.sha256(
        (Path(__file__).resolve().parents[2]/'trading/market/execution_venue.py').read_bytes()).hexdigest()
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


def _completion_json(path, maximum):
    """Read one regular bounded native JSON generation, including open races."""
    import os
    import stat
    path = Path(path)
    before = path.lstat()
    compressed = path.name.endswith('.gz')
    physical_limit = maximum * 2 + 65536 if compressed else maximum
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if not stat.S_ISREG(before.st_mode) or before.st_size > physical_limit:
        raise ValueError('quantity_completion_metadata_invalid')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        if identity(os.fstat(fd)) != identity(before) or not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError('quantity_completion_source_changed')
        with os.fdopen(fd, 'rb', closefd=False) as handle:
            if compressed:
                import gzip
                with gzip.GzipFile(fileobj=handle) as decoder:
                    raw = decoder.read(maximum + 1)
            else:
                raw = handle.read(maximum + 1)
        if ((not compressed and len(raw) != before.st_size) or len(raw) > maximum
                or identity(os.fstat(fd)) != identity(before)
                or identity(path.lstat()) != identity(before)):
            raise ValueError('quantity_completion_source_changed')
    finally:
        os.close(fd)
    claim = Claim(len(raw) * 8)
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError('quantity_completion_metadata_invalid')
    class NativeObject(dict):
        pass
    value = NativeObject(value)
    value.claim = claim
    return value, dict(path=str(path), size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def completion_source_paths(data_dir, day):
    """Canonical native completion inventory, including absent archive variants."""
    directory = Path(data_dir) / 'report/monitor_snapshots'
    raw = directory / f'trade_review_{day}.json'
    sidecar = raw.with_suffix('.completed_projection.json')
    scalar = raw.with_suffix('.fact_projection.json')
    paths = [path for logical in (raw, sidecar, scalar) for path in (
        logical, Path(str(logical)+'.gz'), Path(str(logical)+'.gz.archive_receipt.json'))]
    return paths + [Path(data_dir)/'report/strategy_position_fact_sync'/f'strategy_position_fact_sync_{day}.status.json',
                    Path(str(sidecar)+'.dependencies.json')]


def prepare_completion_cost_revisions(data_dir, first_day, as_of, *, validate_day):
    """Refresh late-cost derivatives once, before the quantity batch is pinned."""
    import re
    from src.engine.lifecycle.holding_window_generation import MAX_METADATA_BYTES
    from src.engine.lifecycle.broker_cost_reconciliation import source_generation
    from src.engine.lifecycle.broker_cost_allocation import refresh_native_research_costs
    from src.engine.lifecycle.broker_cost_source import source_path
    directory = Path(data_dir) / 'report/strategy_position_fact_sync'
    for path in sorted(directory.glob('strategy_position_fact_sync_*.status.json')):
        match = re.fullmatch(r'strategy_position_fact_sync_(\d{4}-\d{2}-\d{2})\.status\.json', path.name)
        if not match or not first_day <= match[1] <= as_of:
            continue
        day = match[1]
        receipt, _ = _completion_json(path, MAX_METADATA_BYTES)
        proof = receipt.get('completion_snapshot_source') or {}
        if proof.get('source_basis') not in {'native_bounded_fact_projection', 'native_original_snapshot_stream'}:
            continue
        # BUY source/index revisions matter even when official costs themselves
        # did not change. Unavailable historical costs are not repair inputs.
        if not receipt.get('completed_census_run_ids'):
            continue
        if (not source_path(Path(data_dir), day).exists()
                and 'quantity_research_cost_generation' not in source_generation(Path(data_dir), day)):
            continue
        issue = validate_day(day)
        if issue is not None:
            raise ValueError('quantity_completion_native_source_invalid:' + day + ':' + str(issue))
        refresh_native_research_costs(Path(data_dir), day, completion_source=proof)


def _legacy_completion_rows(root, day, signature, cache):
    """One native full validation per unchanged original stream generation.

    Signature covers raw/archive/dependency/status identities. Retained compact
    rows keep their existing native budget claims; no current scalar is made.
    """
    from src.engine.lifecycle.main_stop_research_cost import _native_projection
    key = (str(Path(root).resolve()), day, signature)
    if cache is not None and key in cache:
        return cache[key]
    rows, _, _ = _native_projection(Path(root), day)
    if cache is not None:
        cache[key] = rows
    return rows


def _completion_day(data_dir, day, *, read=None, expected=None, legacy_cache=None):
    """Join small native fact seals, without revisiting a historical timeline."""
    import re
    from src.engine import strategy_position_performance_report as facts
    from src.engine.sniper_trade_review_report import completed_census_projection_ids
    from src.engine.lifecycle.holding_window_generation import MAX_METADATA_BYTES, MAX_PROJECTION_BYTES
    from src.engine.lifecycle.snapshot_archive import snapshot_identity
    from src.engine.lifecycle.broker_cost_reconciliation import source_generation, digest, record_source_projector
    directory = Path(data_dir) / 'report/monitor_snapshots'
    raw_path = directory / f'trade_review_{day}.json'
    sidecar = raw_path.with_suffix('.completed_projection.json')
    scalar_path = raw_path.with_suffix('.fact_projection.json')
    status_path = Path(data_dir) / 'report/strategy_position_fact_sync' / f'strategy_position_fact_sync_{day}.status.json'
    dependency_path = Path(str(sidecar) + '.dependencies.json')
    sources = completion_source_paths(data_dir, day)
    before = facts._completion_source_signature(sources)
    def metadata(path, maximum, reference=None):
        if read is None:
            return _completion_json(path, maximum)
        if reference is not None:
            if (reference.get('path') != str(path) or type(reference.get('size')) is not int
                    or not 0 <= reference['size'] <= maximum
                    or re.fullmatch(r'[0-9a-f]{64}', str(reference.get('sha256') or '')) is None):
                raise ValueError('quantity_completion_reference_invalid')
            value = read(path, expected_sha=reference['sha256'], limit=reference['size'])
            return value, reference
        return read(path, limit=maximum), None
    receipt, status_ref = metadata(status_path, MAX_METADATA_BYTES,
        expected.get('fact_receipt') if isinstance(expected, dict) else None)
    if (receipt.get('artifact_sha256') != facts._canonical_sha256({k:v for k,v in receipt.items() if k != 'artifact_sha256'})
            or receipt.get('target_date') != day
            or receipt.get('status') not in {'succeeded', 'valid_empty'}
            or receipt.get('consumer_ready') is not True
            or receipt.get('runtime_effect') is not False
            or receipt.get('allowed_runtime_apply') is not False):
        raise ValueError('quantity_completion_fact_receipt_invalid')
    proof = receipt.get('completion_snapshot_source')
    if not isinstance(proof, dict) or proof.get('source_basis') not in {
            'native_bounded_fact_projection', 'native_original_snapshot_stream'}:
        return None
    legacy = proof['source_basis'] == 'native_original_snapshot_stream'
    if legacy and proof.get('legacy_original_validation') is not None:
        # Earlier entry batches already retain a small native original-source
        # proof. Reuse its full validation contract, including missing costs;
        # never manufacture a dependency receipt or a current fact projection.
        reference = proof['legacy_original_validation']
        guarded = sources + [Path(reference.get('path', '')),
            raw_path.parent/'manifests'/f'monitor_snapshot_manifest_{day}_postclose_exit.json']
        original_guard = facts._completion_source_signature(guarded)
        verified = {}
        observed, issue = facts._legacy_original_generation_issue(day, receipt,
            data_dir=data_dir, validated_proof=verified)
        if not observed or issue is not None:
            raise ValueError('quantity_completion_legacy_source_invalid:' + str(issue))
        value = verified['scalar_projection']
        completed = value['sections']['completed_trade_projection']
        projected = facts._trade_fact_rows_from_report(day, dict(meta=value['meta'],
            sections={'recent_trades':completed, 'completed_trade_projection':completed}))
        if (original_guard != facts._completion_source_signature(guarded)
                or before != facts._completion_source_signature(sources)):
            raise ValueError('quantity_completion_source_changed')
        return projected, dict(schema='initial_quantity_completion_generation_v1', source_date=day,
            fact_receipt=status_ref, completion_snapshot_source=proof)
    dependency, dependency_ref = metadata(dependency_path, MAX_METADATA_BYTES,
        expected.get('dependency_receipt') if isinstance(expected, dict) else None)
    if legacy:
        if proof.get('fact_projection') is not None or dependency.get('fact_projection') is not None:
            raise ValueError('quantity_completion_legacy_projection_conflict')
        rows = _legacy_completion_rows(str(Path(data_dir).resolve()), day,
            digest(before), legacy_cache)
        value = dict(rows.native_header, sections={'completed_trade_projection':list(rows.values())})
        scalar = None
        original_identity = snapshot_identity(raw_path)
    elif read is None:
        physical = scalar_path if scalar_path.exists() else Path(str(scalar_path) + '.gz')
        value, scalar_ref = _completion_json(physical, MAX_PROJECTION_BYTES)
        scalar = {**scalar_ref, 'path': scalar_path.name}
        original_identity = snapshot_identity(raw_path)
    else:
        scalar = proof.get('fact_projection')
        if (not isinstance(scalar, dict) or scalar.get('path') != scalar_path.name
                or type(scalar.get('size')) is not int or not 0 <= scalar['size'] <= MAX_PROJECTION_BYTES
                or re.fullmatch(r'[0-9a-f]{64}', str(scalar.get('sha256') or '')) is None):
            raise ValueError('quantity_completion_scalar_reference_invalid')
        value, _ = metadata(scalar_path, MAX_PROJECTION_BYTES, {**scalar, 'path': str(scalar_path)})
        from src.engine.lifecycle.snapshot_archive import file_identity, SCHEMA
        import stat
        def physical_identity(path):
            current = path.lstat()
            if not stat.S_ISREG(current.st_mode):
                raise ValueError('quantity_completion_physical_source_invalid')
            return file_identity(current)
        if raw_path.exists():
            original_identity = physical_identity(raw_path)
        else:
            archived = Path(str(raw_path) + '.gz')
            archive, _ = metadata(Path(str(archived) + '.archive_receipt.json'), 128 * 1024)
            if (archive.get('schema') != SCHEMA or archive.get('logical_path') != str(raw_path)
                    or archive.get('archive_generation') != physical_identity(archived)
                    or archive.get('runtime_effect') is not False or archive.get('allowed_runtime_apply') is not False
                    or archive.get('logical_size_bytes') != (archive.get('original_identity') or {}).get('size')
                    or re.fullmatch(r'[0-9a-f]{64}', str(archive.get('archive_sha256') or '')) is None
                    or re.fullmatch(r'[0-9a-f]{64}', str(archive.get('logical_content_sha256') or '')) is None):
                raise ValueError('quantity_completion_archive_metadata_invalid')
            original_identity = archive.get('original_identity')
    from src.engine.lifecycle.snapshot_archive import snapshot_identity_matches
    if (original_identity != dependency.get('snapshot_identity')
            and snapshot_identity_matches(raw_path, dependency.get('snapshot_identity'))):
        original_identity = dependency['snapshot_identity']
    costs = source_generation(Path(data_dir), day)
    original_costs = receipt.get('actual_cost_source_generation')
    if any(not isinstance(generation, dict)
            or generation.get('schema') != 'holding_actual_cost_source_generation_v1'
            or generation.get('completion_date') != day
            or type(generation.get('count')) is not int or generation['count'] < 0
            or re.fullmatch(r'[0-9a-f]{64}', str(generation.get('sha256') or '')) is None
            for generation in (costs, original_costs)):
        raise ValueError('quantity_completion_cost_generation_invalid')
    projection = dict(proof.get('projection') or {})
    sealed_dependency = projection.pop('dependency_receipt', None)
    identity = projection.pop('snapshot_identity', None)
    body = {k:v for k,v in value.items() if k != 'artifact_sha256'} if isinstance(value, dict) else {}
    census = (value.get('meta') or {}).get('completed_census_manifest') if isinstance(value, dict) else None
    completed = (value.get('sections') or {}).get('completed_trade_projection') if isinstance(value, dict) else None
    if (not isinstance(original_costs, dict)
            or proof.get('schema') != 'strategy_position_fact_snapshot_source_v1' or proof.get('source_date') != day
            or projection != dependency.get('projection')
            or projection.get('path') != sidecar.name
            or type(projection.get('size')) is not int or projection['size'] < 0
            or re.fullmatch(r'[0-9a-f]{64}', str(projection.get('sha256') or '')) is None
            or sealed_dependency != dict(path=dependency_path.name, size=dependency_ref['size'], sha256=dependency_ref['sha256'])
            or dependency.get('schema') != 'holding_projection_dependency_receipt_v1' or dependency.get('date') != day
            or dependency.get('artifact_sha256') != digest({k:v for k,v in dependency.items() if k != 'artifact_sha256'})
            or identity != dependency.get('snapshot_identity') or identity != original_identity
            or proof.get('fact_projection') != scalar or dependency.get('fact_projection') != scalar
            or not isinstance(value, dict) or value.get('date') != day
            or value.get('snapshot_identity') != identity
            or not legacy and (value.get('schema') != 'trade_review_fact_projection_v1'
                or value.get('source_scope') != 'entered'
                or value.get('artifact_sha256') != facts._canonical_sha256(body)
                or proof.get('scalar_projection_sha256') != value.get('artifact_sha256'))
            or not isinstance(census, dict) or census.get('source_date') != day
            or census.get('schema') != 'trade_review_completed_census_v1'
            or digest(census) != dependency.get('census_sha256')
            or census.get('actual_cost_source_generation') != original_costs
            or (dependency.get('meta') or {}).get('snapshot_profile') != 'postclose_exit'
            or (value.get('meta') or {}).get('snapshot_profile') != 'postclose_exit'
            or receipt.get('completed_census_run_ids') != [census.get('run_id')]
            or receipt.get('completed_census_projection_sha256') != [census.get('projection_sha256')]
            or any(g != original_costs for g in (proof.get('actual_cost_source_generation'),
                       (value.get('meta') or {}).get('actual_cost_source_generation'),
                       (dependency.get('meta') or {}).get('actual_cost_source_generation')))
            or not isinstance(completed, list) or len(completed) != census.get('projected_count')
            or dependency.get('completed_count') != len(completed)
            or (value.get('metrics') or {}).get('canonical_completed_trades') != len(completed)
            or any(not isinstance(row, dict) or row.get('status') != 'COMPLETED'
                   or row.get('completion_observed_date') != day for row in completed)
            or len({str(row.get('id')) for row in completed}) != len(completed)
            or sorted(str(row.get('id')) for row in completed) != completed_census_projection_ids(census)):
        raise ValueError('quantity_completion_projection_binding_invalid')
    census_rows = census.get('rows')
    if (not isinstance(census_rows, list) or len(census_rows) != len(completed)
            or any(not isinstance(row, dict) for row in census_rows)
            or len({str(row.get('id')) for row in census_rows}) != len(completed)):
        raise ValueError('quantity_completion_census_identity_invalid')
    census_by_id = {str(row.get('id')): row for row in census_rows}
    converted = []
    for row in completed:
        sealed = census_by_id.get(str(row.get('id')))
        if (sealed is None or sealed.get('entry_date') != row.get('rec_date')
                or sealed.get('completion_observed_date') != day
                or sealed.get('owner_scope') != row.get('terminal_population_scope')
                or sealed.get('position_tag') != row.get('position_tag')
                or sealed.get('strict_status') != row.get('strict_completion_status')
                or not isinstance(sealed.get('strategy'), str) or not sealed['strategy'].strip()
                or row.get('strategy') not in (None, sealed.get('strategy'))):
            raise ValueError('quantity_completion_owner_census_conflict')
        # Existing native scalar projections deliberately omit strategy; its
        # original value is retained in the exact same sealed census row.
        for key in ('add_count', 'avg_down_count', 'pyramid_count'):
            if key in row and (type(row[key]) is not int or row[key] < 0):
                raise ValueError('quantity_completion_scale_in_count_invalid')
        converted.append({**row, 'strategy': sealed['strategy']})
    native = dict(schema='initial_quantity_completion_generation_v1', source_date=day,
                  fact_receipt=status_ref, dependency_receipt=dependency_ref,
                  completion_snapshot_source=proof)
    revised = costs != original_costs
    if revised:
        native['current_cost_generation'] = costs
    project_costs = record_source_projector(costs) if revised else None
    current_refs = (costs.get('quantity_research_cost_generation') or {}).get('receipts', [])
    current_refs_by_id = {ref['record_id']:ref for ref in current_refs}
    if len(current_refs_by_id) != len(current_refs):
        raise ValueError('quantity_completion_cost_receipt_population_invalid')
    projected = facts._trade_fact_rows_from_report(day, {
        'meta': value['meta'], 'sections': {'recent_trades': converted,
                                          'completed_trade_projection': converted}})
    originals = {str(row['id']): row for row in converted}
    for terminal in projected:
        source = originals[str(terminal['recommendation_id'])]
        if 'quantity_research_cost' in source:
            terminal['quantity_research_cost'] = source['quantity_research_cost']
        if revised:
            # An original terminal remains a fact after costs change, but its
            # old actual economics cannot be relabeled as current. Only the
            # current immutable research receipt may supply research money.
            terminal.update(profit_rate=None, realized_pnl_krw=None,
                broker_actual_fees_taxes_krw=None, economics_source_status='actual_cost_revision_pending',
                actual_cost_reconciliation_status='actual_cost_unallocated')
            terminal.pop('quantity_research_cost', None)
            ref = current_refs_by_id.get(str(source['id']))
            if ref is not None:
                path = Path(data_dir) / 'runtime/initial_quantity_research_costs' / day / 'generations' / (ref['content_sha256'] + '.json')
                current, reference = metadata(path, 256 * 1024)
                if (digest(current) != ref['content_sha256']
                        or reference is not None and reference['sha256'] != ref['sha256']):
                    raise ValueError('quantity_completion_cost_receipt_changed')
                terminal['quantity_research_cost'] = current
            terminal['actual_cost_source_generation'] = project_costs(str(source['id']), terminal.get('quantity_research_cost'))
        for key in ('add_count', 'avg_down_count', 'pyramid_count'):
            if key not in source:
                terminal.pop(key, None)
    if before != facts._completion_source_signature(sources) or costs != source_generation(Path(data_dir), day):
        raise ValueError('quantity_completion_source_changed')
    return projected, native


def verify_completion_overlay_generations(generations, *, data_dir, read=None, legacy_cache=None):
    """Bounded monitor/replay parity; native full validation stays separate."""
    if not isinstance(generations, dict):
        raise ValueError('quantity_completion_generations_invalid')
    verified = {}
    for day, expected in generations.items():
        if datetime.fromisoformat(day).date().isoformat() != day:
            raise ValueError('quantity_completion_date_invalid')
        current = _completion_day(data_dir, day, read=read, expected=expected, legacy_cache=legacy_cache)
        if current is None or current[1] != expected:
            raise ValueError('quantity_completion_generation_changed')
        verified[day] = current[0]
    return verified


def completion_overlay(rows, *, as_of, data_dir, entry_on_or_after, entry_generations, validate_day,
                       source_generations=None):
    """Apply exact completion-date observations to a memory-only as-of census.

    Entry-day facts and DB history remain immutable. Their invalid source proof
    remains invalid even if a later terminal observation is independently valid.
    """
    import re
    from collections import Counter
    from src.engine import strategy_position_performance_report as facts
    from src.engine.scalping.initial_quantity_policy import _timestamp, _number
    from src.engine.lifecycle.holding_window_generation import MAX_METADATA_BYTES
    original = list(rows)
    original_by_id = {str(row['recommendation_id']): row for row in original}
    current = {str(row['recommendation_id']): dict(row) for row in original}
    if len(current) != len(original):
        raise ValueError('quantity_completion_entry_identity_conflict')
    if source_generations is not None:
        for row in current.values():
            observations = row.pop('completion_scale_in_observations', {})
            if not isinstance(observations, dict) or any(key not in {
                    'add_count', 'avg_down_count', 'pyramid_count'} for key in observations):
                raise ValueError('quantity_completion_scale_in_count_invalid')
            # A serialized row holds the latest native count, not its original
            # entry value. Rebuild observed counts from the first sealed native
            # observation; the unknown original count is never replaced by 0.
            # Counts with no native observation retain their entry evidence.
            for key in observations:
                row.pop(key, None)
    generations, seen_terminal, overlays = {}, {}, set()
    native_ids, excluded_terminals = set(), Counter()
    native_observation_count = 0
    original_counts = dict(Counter(str(row.get('original_fact_status', row.get('status'))) for row in original))
    # Reconstructing a pinned replay uses the same terminal join, with bounded
    # receipt/scalar reads. It does not repeat the native large-source hashes.
    decoded, legacy_cache = {}, {}
    # Pinned reconstruction validates an already admitted cohort. Keep only
    # this date's decoded documents; historical rows that differ from their
    # final version retain their document owners until a later observation
    # replaces them, so a retained receipt never outlives its budget claim.
    historical_documents = {}
    def bounded_read(path, *, expected_sha=None, limit):
        physical = path if path.exists() else Path(str(path) + '.gz')
        signature = facts._completion_source_signature([path, Path(str(path) + '.gz')])
        key = (str(path), expected_sha, limit)
        cached = decoded.get(key)
        if cached is not None and cached[0] == signature:
            return cached[1]
        value, reference = _completion_json(physical, limit)
        if expected_sha is not None and reference['sha256'] != expected_sha:
            raise ValueError('quantity_completion_generation_changed')
        if signature != facts._completion_source_signature([path, Path(str(path) + '.gz')]):
            raise ValueError('quantity_completion_source_changed')
        decoded[key] = (signature, value)
        return value
    receipt_dir = Path(data_dir) / 'report/strategy_position_fact_sync'
    for scalar in (Path(data_dir) / 'report/monitor_snapshots').glob('trade_review_*.fact_projection.json*'):
        match = re.fullmatch(r'trade_review_(\d{4}-\d{2}-\d{2})\.fact_projection\.json(?:\.gz)?', scalar.name)
        if (match and entry_on_or_after <= match[1] <= as_of
                and not (receipt_dir / f'strategy_position_fact_sync_{match[1]}.status.json').exists()):
            raise ValueError('quantity_completion_fact_receipt_missing')
    for path in sorted(receipt_dir.glob('strategy_position_fact_sync_*.status.json')):
        match = re.fullmatch(r'strategy_position_fact_sync_(\d{4}-\d{2}-\d{2})\.status\.json', path.name)
        if not match:
            continue
        day = match[1]
        if not entry_on_or_after <= day <= as_of:
            continue
        if source_generations is not None:
            decoded.clear()
        receipt, _ = _completion_json(path, MAX_METADATA_BYTES)
        proof = receipt.get('completion_snapshot_source')
        if proof is None:
            continue
        if not isinstance(proof, dict) or proof.get('source_basis') not in {
                'native_bounded_fact_projection', 'native_original_snapshot_stream'}:
            raise ValueError('quantity_completion_source_basis_invalid')
        if source_generations is not None and day not in source_generations:
            raise ValueError('quantity_completion_generation_changed')
        issue = (entry_generations.get(day, {}).get('issue') if day in entry_generations
                 else validate_day(day) if source_generations is None else None)
        if issue is not None:
            raise ValueError('quantity_completion_native_source_invalid:' + day + ':' + str(issue))
        loaded = _completion_day(data_dir, day,
            read=bounded_read if source_generations is not None else None,
            expected=source_generations.get(day) if source_generations is not None else None,
            legacy_cache=legacy_cache)
        if loaded is None:
            raise ValueError('quantity_completion_projection_missing')
        completed, generation = loaded
        generations[day] = generation
        generation_reference = completion_generation_reference(generation)
        native_observation_count += len(completed)
        for terminal in completed:
            rid = str(terminal['recommendation_id'])
            native_ids.add(rid)
            if not completion_fact_scope(terminal):
                outside = ('other_strategy' if str(terminal['strategy']).upper() not in QUANTITY_FACT_STRATEGIES
                           else 'other_custody')
                if rid in current:
                    raise ValueError('quantity_completion_entry_binding_conflict')
                excluded_terminals[outside] += 1
                continue
            entry = terminal['rec_date'].isoformat()
            buy_at = _timestamp(terminal['buy_time'])
            if buy_at is None:
                raise ValueError('quantity_completion_entry_clock_invalid')
            if not entry_on_or_after <= buy_at.date().isoformat() <= as_of:
                excluded_terminals['outside_actual_entry_window'] += 1
                continue
            rid = str(terminal['recommendation_id'])
            source = current.get(rid)
            if source is None:
                raise ValueError('quantity_completion_entry_fact_missing')
            identity = ('stock_code', 'strategy', 'position_tag', 'buy_price', 'buy_qty')
            normalize = lambda k,v: facts.normalize_strategy(v) if k == 'strategy' else (str(v).upper() if k == 'position_tag' else v)
            if (entry != str(source['rec_date'])
                    or any(normalize(k,terminal[k]) != normalize(k,source.get(k)) for k in identity)
                    or _timestamp(terminal['buy_time']) != _timestamp(source.get('buy_time'))):
                raise ValueError('quantity_completion_entry_binding_conflict')
            buy, sell = _timestamp(terminal['buy_time']), _timestamp(terminal['sell_time'])
            if (buy is None or sell is None or not buy < sell
                    or sell.date().isoformat() > day or day > as_of
                    or _number(terminal['sell_price']) is None or terminal['sell_price'] <= 0):
                raise ValueError('quantity_completion_terminal_clock_invalid')
            fixed_terminal = (str(terminal['rec_date']), terminal['stock_code'], terminal['buy_price'],
                              terminal['buy_qty'], buy.isoformat(), terminal['sell_price'], sell.isoformat())
            if rid in seen_terminal and seen_terminal[rid] != fixed_terminal:
                raise ValueError('quantity_completion_terminal_identity_conflict')
            seen_terminal[rid] = fixed_terminal
            if str(source.get('status')).upper() == 'COMPLETED':
                if (_timestamp(source.get('sell_time')) != sell
                        or _number(source.get('sell_price')) != _number(terminal['sell_price'])):
                    raise ValueError('quantity_completion_original_terminal_conflict')
            original_status = source.get('original_fact_status', source.get('status'))
            updated = dict(source)
            observed_counts = []
            count_sources = dict(source.get('completion_scale_in_observations') or {})
            for key in ('add_count', 'avg_down_count', 'pyramid_count'):
                if key in terminal:
                    original_count = _number(source.get(key))
                    if original_count is not None and terminal[key] < original_count:
                        raise ValueError('quantity_completion_scale_in_count_conflict')
                    updated[key] = terminal[key]
                    count_sources[key] = {'source_date': day, 'value': terminal[key]}
                    observed_counts.append(key)
            for key in ('status', 'sell_price', 'sell_time', 'profit_rate', 'realized_pnl_krw',
                        'economics_source_status', 'actual_cost_reconciliation_status', 'actual_cost_source_generation',
                        'completion_census_run_id', 'completion_census_projection_sha256', 'broker_actual_fees_taxes_krw'):
                value = terminal.get(key)
                updated[key] = value.isoformat() if isinstance(value, datetime) else value
            # Research receipts never change canonical actual economics. A newer
            # terminal without one must also clear any stale inherited receipt.
            if 'quantity_research_cost' in terminal:
                updated['quantity_research_cost'] = terminal['quantity_research_cost']
            else:
                updated.pop('quantity_research_cost', None)
            updated.update(original_fact_status=original_status, completion_source_date=day,
                           completion_generation=generation_reference,
                           completion_observed_scale_in_fields=observed_counts,
                           completion_scale_in_observations=count_sources)
            if source_generations is not None:
                if updated == original_by_id[rid]:
                    # These are the exact same admitted immutable row objects,
                    # not an unaccounted second copy of the allocation receipts.
                    updated = original_by_id[rid]
                    historical_documents.pop(rid, None)
                else:
                    historical_documents[rid] = tuple(item[1] for item in decoded.values())
            current[rid] = updated
            if original_status != 'COMPLETED':
                overlays.add(rid)
        if source_generations is not None:
            loaded = completed = terminal = None
            decoded.clear()
    if source_generations is not None and generations != source_generations:
        raise ValueError('quantity_completion_generation_changed')
    if source_generations is not None and any(row.get('completion_generation')
            and str(row['recommendation_id']) not in seen_terminal for row in original):
        raise ValueError('quantity_completion_entry_binding_conflict')
    if source_generations is not None:
        if list(current.values()) != original:
            raise ValueError('quantity_shared_fact_census_mismatch')
        historical_documents.clear()
        for day, expected in generations.items():
            decoded.clear()
            verify_completion_overlay_generations({day: expected}, data_dir=data_dir, read=bounded_read,
                legacy_cache=legacy_cache)
        decoded.clear()
        result = ResidentFacts(original, claim=rows.claim if isinstance(rows, ResidentFacts) else None)
    else:
        verify_completion_overlay_generations(generations, data_dir=data_dir, legacy_cache=legacy_cache)
        result = ResidentFacts(list(current.values()))
    if any('quantity_research_cost_generation' in (gen.get('cost_generation') or {})
           for gen in entry_generations.values() if isinstance(gen, dict)):
        result.persisted_fact_generations = entry_generations
    result.completion_generations = generations
    result.completion_overlay_summary = dict(schema='initial_quantity_completion_overlay_v1',
        as_of=as_of, overlaid_record_ids=sorted(overlays), overlaid_completed_count=len(overlays),
        native_terminal_record_count=len(native_ids),
        native_terminal_observation_count=native_observation_count,
        applicable_terminal_record_count=len(seen_terminal),
        excluded_native_terminal_observation_counts=dict(excluded_terminals),
        original_fact_status_counts=original_counts,
        current_fact_status_counts=dict(Counter(str(row.get('status')) for row in result)),
        source_scope='entry_day_facts_plus_exact_completion_date_observations',
        entry_day_database_or_source_mutation=False)
    return result


def verify_completion_census_context(rows, census, *, as_of, data_dir, entry_on_or_after):
    """Reproduce serialized overlay claims from small native terminal receipts.

    The original entry status is retained evidence, never a new DB attestation.
    Exact current completion scalars, economics, custody and full populations
    are independently joined by the existing overlay owner.
    """
    from src.engine import strategy_position_performance_report as facts
    from src.engine.lifecycle.broker_cost_reconciliation import source_generation
    from src.engine.scalping.initial_quantity_policy import _digest
    import re
    root = Path(data_dir)
    generations = census.get('completion_overlay_generations', {})
    summary = census.get('completion_overlay_summary', {})
    if (not isinstance(generations, dict) or not isinstance(summary, dict)
            or generations and not summary):
        raise ValueError('quantity_shared_fact_census_mismatch')
    if not generations and not summary:
        if any(isinstance(row, dict) and row.get('completion_generation') for row in rows):
            raise ValueError('quantity_shared_fact_census_mismatch')
    start = entry_on_or_after or '2026-06-05'
    if any(not isinstance(day, str) or datetime.fromisoformat(day).date().isoformat() != day
           or not start <= day <= as_of for day in generations):
        raise ValueError('quantity_shared_fact_census_mismatch')
    def generation():
        paths = []
        for directory, pattern in ((root/'report/strategy_position_fact_sync', 'strategy_position_fact_sync_*.status.json'),
                                   (root/'report/monitor_snapshots', 'trade_review_*.fact_projection.json*')):
            for path in directory.glob(pattern):
                match = re.search(r'(\d{4}-\d{2}-\d{2})', path.name)
                if match and start <= match[1] <= as_of:
                    paths.append(path)
        for day in generations:
            raw = root/'report/monitor_snapshots'/f'trade_review_{day}.json'
            sidecar = raw.with_suffix('.completed_projection.json')
            scalar = raw.with_suffix('.fact_projection.json')
            paths.extend(p for logical in (raw, sidecar, scalar) for p in (
                logical, Path(str(logical)+'.gz'), Path(str(logical)+'.gz.archive_receipt.json')))
            paths.append(Path(str(sidecar)+'.dependencies.json'))
        return (facts._completion_source_signature(sorted(set(paths))),
                {day:source_generation(root, day) for day in generations})
    before = generation()
    key = (str(root.resolve()), as_of, start, _digest(census))
    if _VERIFIED_COMPLETION_CONTEXTS.get(key) != before:
        reconstructed = completion_overlay(rows, as_of=as_of, data_dir=root,
            entry_on_or_after=start, entry_generations=census.get('persisted_fact_generations', {}),
            validate_day=None, source_generations=generations)
        if (list(reconstructed) != list(rows) or reconstructed.completion_generations != generations
                or summary and reconstructed.completion_overlay_summary != summary):
            raise ValueError('quantity_shared_fact_census_mismatch')
    if generation() != before:
        raise ValueError('quantity_completion_source_changed')
    _VERIFIED_COMPLETION_CONTEXTS[key] = before
    _VERIFIED_COMPLETION_CONTEXTS.move_to_end(key)
    while len(_VERIFIED_COMPLETION_CONTEXTS) > 8:
        _VERIFIED_COMPLETION_CONTEXTS.popitem(last=False)
