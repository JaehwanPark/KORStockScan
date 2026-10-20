"""Producer-verified bounded quantity observations; never policy inputs.

Full immutable reports remain the authority. Only their publishing worker runs
the full native and semantic gates. Readers check that proof, exact source file
identities and current cost generations, without reopening large child reports.
This has the same local trusted-writer boundary as entry_split_monitor_projection.
"""
from __future__ import annotations

from collections import Counter
import fcntl
import hashlib
import json
import os
import re
from pathlib import Path

from src.engine.scalping import entry_split_monitor_projection as files

SCHEMA = 'initial_quantity_monitor_projection_v1'
RECEIPT = 'initial_quantity_monitor_validation_v1'
MANIFEST = 'initial_quantity_monitor_manifest_v1'
# Structured native metadata uses the existing 4MiB child budget. Original
# reports/timeouts keep their larger producer limits and are never warm-read.
MAX_BYTES = 4 * 1024 * 1024
MAX_REFERENCES = 8192
CHILD_LIMIT = 4 * 1024 * 1024


def manifest_path(stage_path, *, code=None):
    suffix = '.monitor.json' if code is None else '.monitor.' + _digest(code) + '.json'
    return Path(stage_path).with_suffix(suffix)


def _digest(value):
    return hashlib.sha256(files._canonical(value)).hexdigest()


def _native_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _code():
    from src.engine.lifecycle.holding_window_generation import cached_code_generation
    engine = Path(__file__).resolve().parents[1]
    names = set('''scalping/initial_quantity_monitor_projection.py
automation/main_trailing_source_store.py
scalping/entry_split_monitor_projection.py
scalping/initial_quantity_policy.py
scalping/initial_quantity_source_cache.py
scalping/initial_quantity_refresh_evaluation.py
scalping/initial_quantity_timeout_research.py
scalping/initial_quantity_following_bars.py
scalping/initial_quantity_timeout.py
scalping/initial_quantity_activation.py
scalping/initial_quantity_legacy_reader.py
scalping/initial_quantity_cap_observation.py
scalping/initial_quantity_type.py
scalping/entry_execution_sizing_plan.py
scalping/entry_split_order_plan.py
scalping/pre_submit_delay_initial_policy.py
scalping/mechanistic_entry_runtime_policy.py
lifecycle/broker_cost_reconciliation.py
lifecycle/broker_cost_allocation.py
lifecycle/broker_cost_source.py
lifecycle/holding_window_generation.py
lifecycle/research_storage.py
lifecycle/research_input_budget.py
lifecycle/research_json_stream.py
lifecycle/research_disk_budget.py
lifecycle/snapshot_archive.py
infrastructure/validation_digest_session.py
strategy_position_performance_report.py
sniper_trade_review_report.py
sniper_execution_receipts.py
sniper_position_tags.py
log_archive_service.py
monitor_snapshot_runtime.py
trade_profit.py
error_detectors/artifact_freshness.py'''.split())
    from src.engine.scalping.initial_quantity_refresh_evaluation import EXECUTION_READERS
    names.update('scalping/'+name for name in EXECUTION_READERS)
    paths = [engine/name for name in sorted(names)]
    paths.extend(engine.parent/relative for relative in (
        'trading/order/tick_utils.py', 'trading/order/split_execution_math.py',
        'trading/market/execution_venue.py',
        'utils/jsonl_io.py'))
    observed = cached_code_generation(paths)
    return {str(path.relative_to(engine.parent)): observed[str(path)] for path in paths}


def _identity(path):
    path = Path(path)
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise ValueError('quantity_monitor_source_symlink')
    if not path.exists():
        return None
    full = files._identity(path)
    return {'stat': [full[key] for key in
        ('dev', 'ino', 'size', 'mtime_ns', 'ctime_ns', 'mode', 'uid', 'gid', 'nlink')],
        'parent': [full['parent_dev'], full['parent_ino']]}


def _dependencies(stage_path, stage, report, data_root):
    """Exact known native source inventory, including absent archive variants."""
    from src.engine.scalping.initial_quantity_source_cache import completion_source_paths
    from src.engine.scalping.mechanistic_entry_runtime_policy import is_pipeline_source_reference
    from src.engine.lifecycle.holding_window_generation import MAX_METADATA_BYTES
    paths = {Path(stage_path)}
    paths.update(Path(value) for key, value in stage.items()
                 if key.endswith('_path') and isinstance(value, str))
    census = report.get('census') or {}
    entries = census.get('persisted_fact_generations', {})
    completions = census.get('completion_overlay_generations', {})
    for day in set(entries) | set(completions):
        paths.update(completion_source_paths(data_root, day))
        paths.add(Path(data_root)/'report/monitor_snapshots/manifests'/
            ('monitor_snapshot_manifest_'+day+'_postclose_exit.json'))
        status_path = (Path(data_root)/'report/strategy_position_fact_sync'/
            ('strategy_position_fact_sync_'+day+'.status.json'))
        if status_path.is_file() and not status_path.is_symlink() and status_path.stat().st_size <= MAX_METADATA_BYTES:
            try:
                status, _ = files._read(status_path, MAX_METADATA_BYTES)
            except (OSError, ValueError):
                # A native-known invalid fact status can legitimately produce
                # a source-gap stage; pin its bytes/identity without inventing
                # any deeper proof that its own parser rejected.
                status = {}
            legacy = ((status.get('completion_snapshot_source') or {}).get('legacy_original_validation') or {})
            if isinstance(legacy, dict) and isinstance(legacy.get('path'), str):
                candidate = Path(legacy['path'])
                expected = status_path.parent/'legacy_sources'/day
                if (candidate.is_absolute() and candidate.parent == expected
                        and candidate.suffix == '.json' and len(candidate.stem) == 64
                        and all(letter in '0123456789abcdef' for letter in candidate.stem)):
                    paths.add(candidate)
    for generation in entries.values():
        if generation.get('path'):
            paths.add(Path(generation['path']))
    for key in ('source_quality_by_entry_date', 'source_quality_by_exit_date'):
        for generation in census.get(key, {}).values():
            if generation.get('artifact'):
                paths.add(Path(generation['artifact']))
    for generation in (report.get('pipeline_source_receipts') or {}).values():
        if generation.get('path') and not is_pipeline_source_reference(generation['path'], data_root=data_root):
            paths.add(Path(generation['path']))
        lifecycle = generation.get('capture_lifecycle_generation') or {}
        paths.update(Path(item['path']) for item in lifecycle.get('files', []))
    pid = stage.get('pid_receipt') or {}
    for receipt in pid.get('daily_pid_receipts', []):
        if receipt.get('archive_path'):
            paths.add(Path(receipt['archive_path']))
        elif pid.get('data_root') and receipt.get('entry_date'):
            base = Path(pid['data_root'])/'runtime/policy_bootstrap'
            day = receipt['entry_date']
            paths.update((base/('runtime_policy_bootstrap_'+day+'.json'),
                base/('runtime_policy_bootstrap_'+day+'.env'),
                base/('runtime_policy_bootstrap_verify_'+day+'.json')))
    if len(paths) > MAX_REFERENCES or any(not path.is_absolute() for path in paths):
        raise ValueError('quantity_monitor_reference_budget_or_path')
    return {str(path): _identity(path) for path in sorted(paths)}


def _directories(report, data_root):
    result = {}
    for generation in (report.get('pipeline_source_receipts') or {}).values():
        lifecycle = generation.get('capture_lifecycle_generation')
        if lifecycle is None:
            continue
        path = Path(data_root)/'runtime/initial_quantity/cap_capture_receipts'/lifecycle['source_date']
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
            raise ValueError('quantity_monitor_source_symlink')
        names = sorted(item.name for item in path.glob('*.json')) if path.exists() else []
        if len(names) > 4096:
            raise ValueError('quantity_monitor_lifecycle_budget')
        result[str(path)] = {'exists': path.exists(), 'files': names}
    return result


def _snapshot_sources(dependencies, data_root):
    """Cold publisher binds logical bytes once; warm readers use native custody."""
    from src.engine.lifecycle import snapshot_archive as archive
    parent = Path(data_root)/'report/monitor_snapshots'
    result = {}
    for name in dependencies:
        path = Path(name)
        if path.parent != parent or not re.fullmatch(
                r'trade_review_\d{4}-\d{2}-\d{2}(?:\.completed_projection)?\.json', path.name):
            continue
        aliases = [str(path), str(path)+'.gz', str(path)+'.gz.archive_receipt.json']
        if not all(alias in dependencies for alias in aliases):
            continue
        if path.exists():
            generation = archive.generation(path)
            identity = archive.file_identity(path.stat())
        elif Path(aliases[1]).exists():
            receipt = archive.archived_receipt(path)
            generation = dict(path=path.name, size=receipt['logical_size_bytes'],
                              sha256=receipt['logical_content_sha256'])
            identity = receipt['original_identity']
        else:
            continue
        result[name] = dict(generation=generation, original_identity=identity)
    return result


def _verified_dependencies(dependencies, snapshots, data_root):
    """Accept only native lossless representation changes of cold-bound bytes."""
    from src.engine.lifecycle import snapshot_archive as archive
    observed = {name: _identity(Path(name)) for name in dependencies}
    parent = Path(data_root)/'report/monitor_snapshots'
    for name, bound in snapshots.items():
        path = Path(name)
        aliases = [name, name+'.gz', name+'.gz.archive_receipt.json']
        if (path.parent != parent or not re.fullmatch(
                r'trade_review_\d{4}-\d{2}-\d{2}(?:\.completed_projection)?\.json', path.name)
                or not all(alias in dependencies for alias in aliases)):
            raise ValueError('quantity_monitor_logical_source_path_invalid')
        if all(observed[alias] == dependencies[alias] for alias in aliases):
            continue
        if observed[name] is not None or any(observed[alias] is None for alias in aliases[1:]):
            raise ValueError('quantity_monitor_source_changed')
        receipt = archive.archived_receipt(path, bound_logical_generation=bound['generation'])
        if receipt['original_identity'] != bound['original_identity']:
            raise ValueError('quantity_monitor_source_changed')
        # Only these three physical names moved. All unrelated source, cost,
        # directory and issued-stage identities retain their strict checks.
        for alias in aliases:
            observed[alias] = dependencies[alias]
    return observed


def _check_directories(expected):
    for name, generation in expected.items():
        path = Path(name)
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
            raise ValueError('quantity_monitor_source_symlink')
        names = sorted(item.name for item in path.glob('*.json')) if path.exists() else []
        if len(names) > 4096 or {'exists': path.exists(), 'files': names} != generation:
            raise ValueError('quantity_monitor_lifecycle_changed')


def _cost_signature(data_root, costs):
    """Compact physical census of exactly the cold-verified cost inputs."""
    root = Path(data_root)
    output = {}
    def file(path):
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
            raise ValueError('quantity_monitor_cost_source_symlink')
        if not path.exists():
            return None
        info = path.stat()
        import stat
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('quantity_monitor_cost_source_regular_required')
        return [getattr(info, 'st_'+key) for key in
                ('dev', 'ino', 'size', 'mtime_ns', 'ctime_ns', 'mode', 'uid', 'gid', 'nlink')]
    paths = set()
    for item in costs:
        day = item['source_date']
        actual = root/'runtime/holding_actual_costs'/day
        if actual.is_symlink():
            raise ValueError('quantity_monitor_cost_source_symlink')
        names = sorted(p.name for p in actual.glob('*.json')) if actual.exists() else []
        if len(names) > 10000:
            raise ValueError('quantity_monitor_cost_source_count')
        output[str(actual)] = {'files': names, 'exists': actual.exists()}
        paths.update(actual/name for name in names)
        research = root/'runtime/initial_quantity_research_costs'/day
        paths.add(research/'index.json')
        paths.add(root/'runtime/holding_broker_cost_sources'/(day+'.json'))
        for source in item['generation'].get('quantity_research_cost_generation', {}).get('source_dates', []):
            paths.add(root/'runtime/holding_broker_cost_sources'/(source['source_date']+'.json'))
        for receipt in item['generation'].get('quantity_research_cost_generation', {}).get('receipts', []):
            paths.add(research/'generations'/(receipt['content_sha256']+'.json'))
    if len(paths) > 20000:
        raise ValueError('quantity_monitor_cost_source_count')
    # Group common parent paths; 1000 admitted receipts stay well below 1MiB.
    for path in sorted(paths):
        output.setdefault(str(path.parent), {}).setdefault('entries', {})[path.name] = file(path)
    return output


def _costs(report, data_root):
    from src.engine.lifecycle.broker_cost_reconciliation import source_generation
    census = report.get('census') or {}
    expected = []
    for day, generation in census.get('persisted_fact_generations', {}).items():
        if isinstance(generation, dict) and isinstance(generation.get('cost_generation'), dict):
            expected.append({'source_date': day, 'generation': generation['cost_generation']})
    for day, generation in census.get('completion_overlay_generations', {}).items():
        costs = generation.get('current_cost_generation',
            (generation.get('completion_snapshot_source') or {}).get('actual_cost_source_generation'))
        if isinstance(costs, dict):
            expected.append({'source_date': day, 'generation': costs})
    expected = list({(item['source_date'], _digest(item['generation'])): item
                     for item in expected}.values())
    # Each of the native 256 dates may have distinct entry/completion views.
    if len(expected) > 512:
        raise ValueError('quantity_monitor_cost_date_budget')
    for item in expected:
        costs, day = item['generation'], item['source_date']
        dates = costs.get('quantity_research_cost_generation', {}).get('source_dates')
        kwargs = {'additional_source_dates': [row['source_date'] for row in dates]} if dates is not None else {}
        if source_generation(data_root, day, **kwargs) != costs:
            raise ValueError('quantity_monitor_cost_generation_changed')
    return expected


def _observation(stage, report, evaluation, data_root):
    from src.engine.error_detectors.artifact_freshness import _quantity_postclose_stage_observation
    def bounded_read(path, *, limit=1024*1024, expected_sha=None):
        value, record = files._read(Path(path), limit)
        if expected_sha is not None and record['sha256'] != expected_sha:
            raise ValueError('quantity_monitor_native_source_changed')
        return value
    return _quantity_postclose_stage_observation(Path(data_root).parent,
        stage['source_date'], stage, report, evaluation, bounded_read)


def _historical_exclusions(stage, observation, disposition, input_manifest):
    """Classify an explicitly accepted, isolated historical population only.

    The original gap, economic exclusions and null economics remain evidence.
    Source/code freshness is still checked by the enclosing native projection.
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo
    rows = disposition.get('excluded_rows', [])
    accepted = datetime.fromisoformat(disposition['accepted_at'])
    counts = Counter(row['reason'] for row in rows)
    if (disposition.get('schema') != 'initial_quantity_historical_exclusions_v1'
            or disposition.get('disposition') != 'excluded_from_economic_sample'
            or disposition.get('source_date') != stage.get('source_date')
            or disposition.get('stage_content_sha256') != stage.get('receipt_content_sha256')
            or disposition.get('report_content_sha256') != stage.get('report_content_sha256')
            or disposition.get('input_manifest_sha256') != input_manifest
            or accepted.tzinfo is None or accepted > datetime.now(ZoneInfo('Asia/Seoul'))
            or stage['source_date'] >= accepted.astimezone(ZoneInfo('Asia/Seoul')).date().isoformat()
            or stage.get('generation_kind') != 'refresh'
            or stage.get('stage_status') != 'complete_source_only' or stage.get('terminal') is not True
            or any(stage.get(key) is not False for key in
                   ('runtime_apply_allowed', 'runtime_effect', 'actual_order_submitted'))
            or stage.get('decision') != 'carry_parent'
            or observation.get('economic_sample_status') != 'cost_eligible'
            or observation.get('trade_policy_binding_status') != 'bound'
            or observation.get('postclose_completed_trade_count', 0) <= 0
            or observation.get('postclose_semantic_findings') != ['initial_quantity_economic_source_gap']
            or not rows or len({row['record_id'] for row in rows}) != len(rows)
            or any(not row['record_id'] or not row['stock_code']
                   or len(row['fact_sha256']) != 64 for row in rows)
            or set(counts) - {'terminal_cost_or_quantity_missing', 'quantity_research_cost_invalid'}
            or dict(counts) != observation.get('postclose_source_gap_reasons')
            or dict(counts) != disposition.get('exclusion_counts')):
        raise ValueError('quantity_historical_exclusions_binding_invalid')
    return {**observation, 'postclose_semantic_findings': [],
        'postclose_historical_diagnostics': observation['postclose_semantic_findings'],
        'postclose_attention_status': 'historical_exclusions_recorded',
        'postclose_historical_exclusions': disposition}


def _exclusion_disposition(stage_path, stage, report, observation, data_root, record_ids):
    """Reuse an exact prior acknowledgement, or issue one on explicit request."""
    from src.engine.scalping import initial_quantity_policy as native
    from datetime import datetime
    from zoneinfo import ZoneInfo
    disposition = None
    if record_ids is None and manifest_path(stage_path).exists():
        pointer, _ = files._read(manifest_path(stage_path), 65536)
        selected = Path(pointer['projection_path'])
        if (selected.parent != Path(stage_path).parent/'monitor_generations'
                or selected.name != pointer['projection_content_sha256']+'.projection.json'):
            raise ValueError('quantity_monitor_projection_path_invalid')
        previous, metadata = files._read(selected, MAX_BYTES)
        if (metadata['sha256'] != pointer['projection_sha256']
                or _digest(previous) != pointer['projection_content_sha256']):
            raise ValueError('quantity_monitor_projection_invalid')
        disposition = previous.get('historical_exclusion_disposition')
    if record_ids is not None or disposition is not None:
        rows = []
        for fact in report['census']['input_fact_rows']:
            _, census = native.completed_trade_fact_census(stage['source_date'],
                fact_rows=[fact], data_dir=data_root,
                entry_on_or_after=report['census'].get('entry_on_or_after'))
            for reason, count in census['excluded'].items():
                if reason in observation['postclose_source_gap_reasons']:
                    if count != 1:
                        raise ValueError('quantity_historical_exclusions_population_invalid')
                    rows.append(dict(record_id=str(fact['recommendation_id']),
                        stock_code=str(fact['stock_code']), fact_sha256=native._digest(fact), reason=reason))
        rows.sort(key=lambda row: row['record_id'])
        if record_ids is not None:
            if sorted(map(str, record_ids)) != [row['record_id'] for row in rows]:
                raise ValueError('quantity_historical_exclusions_population_invalid')
            disposition = dict(schema='initial_quantity_historical_exclusions_v1',
                disposition='excluded_from_economic_sample',
                accepted_at=datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),
                source_date=stage['source_date'], stage_content_sha256=stage['receipt_content_sha256'],
                report_content_sha256=stage['report_content_sha256'],
                input_manifest_sha256=report['census']['input_manifest_sha256'],
                exclusion_counts=dict(Counter(row['reason'] for row in rows)), excluded_rows=rows)
        if disposition['excluded_rows'] != rows:
            raise ValueError('quantity_historical_exclusions_population_changed')
        _historical_exclusions(stage, observation, disposition, report['census']['input_manifest_sha256'])
    return disposition


def publish(stage_path, stage, report, *, data_root, accepted_historical_record_ids=None,
            publish_current=True):
    if type(publish_current) is not bool:
        raise ValueError('quantity_monitor_publication_mode_invalid')
    """Publish a native proof; historical exclusions require explicit acceptance."""
    if (accepted_historical_record_ids is None and not manifest_path(stage_path).exists()
            and not any(Path(stage[name+'_path']).stat().st_size > CHILD_LIMIT
                        for name in ('report', 'timeout_research') if name+'_path' in stage)):
        return None
    from src.engine.scalping import initial_quantity_policy as native
    data_root = Path(data_root).resolve()
    code = _code()
    before = _dependencies(stage_path, stage, report, data_root)
    directories_before = _directories(report, data_root)
    saved_stage, stage_file = files._read(Path(stage_path), MAX_BYTES)
    if saved_stage != stage:
        raise ValueError('quantity_monitor_stage_file_mismatch')
    if (report.get('report_content_sha256') != stage.get('report_content_sha256')
            or _native_digest({key: value for key, value in report.items() if key != 'report_content_sha256'}) != stage['report_content_sha256']):
        raise ValueError('quantity_monitor_report_binding_invalid')
    validate = native.refresh_quantity_stage_terminal_valid if stage.get('generation_kind') == 'refresh' else native.initial_quantity_stage_terminal_valid
    if not validate(stage):
        raise ValueError('quantity_monitor_native_stage_invalid')
    evaluation = json.loads(Path(stage['evaluation_path']).read_bytes()) if 'evaluation_path' in stage else None
    observation = _observation(stage, report, evaluation, data_root)
    issued = {'report': {'source_date': report['source_date'],
        'report_content_sha256': report['report_content_sha256'],
        'census': {'input_manifest_sha256': report['census']['input_manifest_sha256']}}}
    for name in ('candidate', 'candidate_policy', 'parent_policy'):
        if name+'_path' in stage:
            value, _ = files._read(Path(stage[name+'_path']), CHILD_LIMIT)
            issued['candidate' if name == 'candidate_policy' else name] = value
    costs = _costs(report, data_root)
    cost_signature = _cost_signature(data_root, costs)
    snapshots = _snapshot_sources(before, data_root)
    issued_sources = {str(Path(stage_path)): before[str(Path(stage_path))]}
    issued_hashes = {str(Path(stage_path)): stage_file['sha256']}
    for name, child in stage.items():
        if name.endswith('_path'):
            expected = stage.get(name[:-5]+'_file_sha256')
            if not isinstance(expected, str) or len(expected) != 64:
                raise ValueError('quantity_monitor_issued_child_hash_missing')
            issued_sources[str(Path(child))] = before[str(Path(child))]
            issued_hashes[str(Path(child))] = expected
    projection = dict(schema=SCHEMA, source_date=stage['source_date'], data_root=str(data_root),
        stage_content_sha256=stage['receipt_content_sha256'], issued=issued,
        observation=observation,
        coverage=dict(input_fact_count=len(report['census']['input_fact_rows']),
            input_manifest_sha256=report['census']['input_manifest_sha256'],
            trade_count=len(report['trades']), trades_sha256=_digest(report['trades']),
            status_counts=dict(Counter(str(row.get('status')) for row in report['census']['input_fact_rows'])),
            full_native_stage_validated=True, full_semantic_census_validated=True),
        native_validation_scope='full_stage_policy_timeout_census_and_native_completion',
        dependencies=before, logical_snapshot_dependencies=snapshots,
        issued_sources=issued_sources, issued_file_sha256=issued_hashes,
        cost_generations=[{'source_date': item['source_date'],
            'generation_sha256': _digest(item['generation'])} for item in costs],
        cost_source_inventory=cost_signature, source_directories=directories_before, code=code,
        decision_authority='report_only', runtime_effect=False, runtime_apply_allowed=False,
        actual_order_submitted=False)
    if len(files._canonical(projection)) > MAX_BYTES:
        raise ValueError('quantity_monitor_projection_budget')
    if (before != _dependencies(stage_path, stage, report, data_root)
            or directories_before != _directories(report, data_root) or code != _code()):
        raise ValueError('quantity_monitor_source_changed')
    base = Path(stage_path).parent/'monitor_generations'
    base.mkdir(exist_ok=True)
    lock_path = Path(stage_path).parent/'.monitor.lock'
    with os.fdopen(os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600), 'a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if (lock_path.stat().st_dev, lock_path.stat().st_ino) != (os.fstat(lock.fileno()).st_dev, os.fstat(lock.fileno()).st_ino):
            raise ValueError('quantity_monitor_lock_changed')
        if before != _dependencies(stage_path, stage, report, data_root):
            raise ValueError('quantity_monitor_source_changed')
        if costs != _costs(report, data_root) or cost_signature != _cost_signature(data_root, costs) or code != _code():
            raise ValueError('quantity_monitor_cost_generation_changed')
        # Read the prior disposition under the same publisher lock: a refresh
        # that started earlier must not erase a concurrently accepted population.
        disposition = _exclusion_disposition(stage_path, stage, report, observation,
            data_root, accepted_historical_record_ids)
        if disposition is not None:
            projection['historical_exclusion_disposition'] = disposition
        if len(files._canonical(projection)) > MAX_BYTES:
            raise ValueError('quantity_monitor_projection_budget')
        ident = _digest(projection)
        path = base/(ident+'.projection.json')
        files._write_atomic(path, projection, MAX_BYTES, immutable=True)
        pointer = dict(schema=MANIFEST, source_date=stage['source_date'],
            stage_content_sha256=stage['receipt_content_sha256'],
            projection_path=str(path), projection_sha256=native._file_sha256(path),
            projection_content_sha256=ident, code=code,
            decision_authority='report_only', runtime_effect=False, runtime_apply_allowed=False,
            actual_order_submitted=False)
        previous = manifest_path(stage_path)
        if publish_current and previous.exists():
            _, record = files._read(previous, 65536)
            with previous.open('rb') as original:
                old = original.read(65537)
            if len(old) > 65536 or files._identity(previous) != record['identity']:
                raise ValueError('quantity_monitor_manifest_changed')
            archived = base/(hashlib.sha256(old).hexdigest()+'.manifest.json')
            if not archived.exists():
                with archived.open('xb') as handle:
                    handle.write(old)
                    handle.flush(); os.fsync(handle.fileno())
        # A reviewed candidate can prove its own generation before selection
        # without replacing the incumbent reader's manifest. Both consumers
        # retain the same native source, coverage and authority checks.
        files._write_atomic(manifest_path(stage_path, code=code), pointer, 65536)
        if publish_current:
            files._write_atomic(previous, pointer, 65536)
        if (before != _dependencies(stage_path, stage, report, data_root)
                or cost_signature != _cost_signature(data_root, costs)
                or projection['source_directories'] != _directories(report, data_root) or code != _code()):
            raise ValueError('quantity_monitor_source_changed')
    return pointer


def read_verified(stage_path, stage, *, read, data_root=None, role='current_stage'):
    """Return a native proof or None for the unchanged bounded legacy reader."""
    if role not in {'current_stage', 'issued_ancestry'}:
        raise ValueError('quantity_monitor_role_invalid')
    code = _code() if role == 'current_stage' else None
    pointer_path = manifest_path(stage_path, code=code)
    if code is not None and not pointer_path.exists() and not pointer_path.is_symlink():
        pointer_path = manifest_path(stage_path)
    if not pointer_path.exists() and not pointer_path.is_symlink():
        return None
    pointer = read(pointer_path, limit=65536)
    if (pointer.get('schema') != MANIFEST or (role == 'current_stage' and pointer.get('code') != code)
            or pointer.get('source_date') != stage.get('source_date')
            or pointer.get('stage_content_sha256') != stage.get('receipt_content_sha256')):
        raise ValueError('quantity_monitor_manifest_invalid')
    path = Path(pointer['projection_path'])
    if (path.parent != Path(stage_path).parent/'monitor_generations'
            or path.name != pointer.get('projection_content_sha256')+'.projection.json'):
        raise ValueError('quantity_monitor_projection_path_invalid')
    value = read(path, limit=MAX_BYTES, expected_sha=pointer['projection_sha256'])
    if (value.get('schema') != SCHEMA or _digest(value) != pointer['projection_content_sha256']
            or value.get('stage_content_sha256') != stage.get('receipt_content_sha256')
            or value.get('code') != pointer.get('code')
            or not isinstance(value.get('code'), dict) or not value['code']
            or any(not isinstance(name, str) or not isinstance(sha, str) or len(sha) != 64
                   or any(letter not in '0123456789abcdef' for letter in sha)
                   for name, sha in value['code'].items())
            or value.get('native_validation_scope') != 'full_stage_policy_timeout_census_and_native_completion'
            or value.get('coverage', {}).get('full_native_stage_validated') is not True
            or value.get('coverage', {}).get('full_semantic_census_validated') is not True):
        raise ValueError('quantity_monitor_projection_invalid')
    for body in (pointer, value):
        if (body.get('decision_authority') != 'report_only' or body.get('runtime_effect') is not False
                or body.get('runtime_apply_allowed') is not False
                or body.get('actual_order_submitted') is not False):
            raise ValueError('quantity_monitor_authority_invalid')
    coverage, observation = value['coverage'], value['observation']
    if (value.get('source_date') != stage.get('source_date')
            or coverage.get('trade_count') != stage.get('all_completed_initial_trades')
            or coverage.get('trade_count') != observation.get('postclose_completed_trade_count')
            or coverage.get('input_fact_count') != observation.get('postclose_input_fact_count')
            or coverage.get('input_manifest_sha256') != value['issued']['report']['census']['input_manifest_sha256']
            or sum(coverage.get('status_counts', {}).values()) != coverage.get('input_fact_count')
            or coverage.get('input_fact_count') != coverage.get('trade_count') + sum(observation.get('postclose_exclusion_reasons', {}).values())):
        raise ValueError('quantity_monitor_coverage_invalid')
    dependencies = value['dependencies']
    if not isinstance(dependencies, dict) or len(dependencies) > MAX_REFERENCES:
        raise ValueError('quantity_monitor_reference_budget')
    root = Path(value['data_root'])
    if (not root.is_absolute() or root.resolve() != root
            or (data_root is not None and root != Path(data_root).resolve())
            or str(Path(stage_path)) not in dependencies):
        raise ValueError('quantity_monitor_data_root_invalid')
    expected_issued = {str(Path(stage_path))}
    expected_issued.update(str(Path(child)) for name, child in stage.items() if name.endswith('_path'))
    issued_sources, issued_hashes = value.get('issued_sources'), value.get('issued_file_sha256')
    if (not isinstance(issued_sources, dict) or set(issued_sources) != expected_issued
            or not isinstance(issued_hashes, dict) or set(issued_hashes) != expected_issued
            or any(issued_sources[name] != dependencies.get(name) for name in expected_issued)
            or any(issued_hashes[str(Path(child))] != stage.get(name[:-5]+'_file_sha256')
                   for name, child in stage.items() if name.endswith('_path'))):
        raise ValueError('quantity_monitor_issued_binding_invalid')
    issued_before = {name: _identity(Path(name)) for name in issued_sources}
    if issued_before != issued_sources:
        raise ValueError('quantity_monitor_issued_source_changed')
    if read(Path(stage_path), limit=MAX_BYTES, expected_sha=issued_hashes[str(Path(stage_path))]) != stage:
        raise ValueError('quantity_monitor_stage_file_mismatch')
    if role == 'issued_ancestry':
        # An approved policy retains its original issued evidence. Later cost
        # corrections/archives and new native code affect current research,
        # never add a fresh economic or natural-consumption adoption hurdle.
        if issued_before != {name: _identity(Path(name)) for name in issued_sources}:
            raise ValueError('quantity_monitor_issued_source_changed')
        return {'issued': value['issued'], 'observation': value['observation']}
    snapshots = value.get('logical_snapshot_dependencies', {})
    if not isinstance(snapshots, dict) or len(snapshots) > MAX_REFERENCES:
        raise ValueError('quantity_monitor_reference_budget')
    before = _verified_dependencies(dependencies, snapshots, root)
    if before != dependencies:
        raise ValueError('quantity_monitor_source_changed')
    _check_directories(value['source_directories'])
    # Every cold-verified receipt/index/official alias is stat-bound, including
    # absent aliases and the full actual-cost directory census. Warm readers do
    # not repeatedly decode N native receipts, and corrections invalidate proof.
    inventory = value['cost_source_inventory']
    def current_cost_inventory():
        observed = {}
        import stat
        for parent, group in inventory.items():
            directory = Path(parent)
            if not directory.is_relative_to(root/'runtime'):
                raise ValueError('quantity_monitor_cost_source_path_invalid')
            if directory.is_symlink() or any(p.is_symlink() for p in directory.parents):
                raise ValueError('quantity_monitor_cost_source_symlink')
            row = {}
            if 'files' in group:
                row.update(files=sorted(p.name for p in directory.glob('*.json')) if directory.exists() else [], exists=directory.exists())
            for name in group.get('entries', {}):
                if not isinstance(name, str) or Path(name).name != name:
                    raise ValueError('quantity_monitor_cost_source_path_invalid')
                path = directory/name
                if path.is_symlink():
                    raise ValueError('quantity_monitor_cost_source_symlink')
                info = path.stat() if path.exists() else None
                if info is not None and not stat.S_ISREG(info.st_mode):
                    raise ValueError('quantity_monitor_cost_source_regular_required')
                row.setdefault('entries', {})[name] = None if info is None else [getattr(info, 'st_'+key) for key in
                    ('dev', 'ino', 'size', 'mtime_ns', 'ctime_ns', 'mode', 'uid', 'gid', 'nlink')]
            observed[parent] = row
        return observed
    if current_cost_inventory() != inventory:
        raise ValueError('quantity_monitor_cost_generation_changed')
    if (before != _verified_dependencies(dependencies, snapshots, root)
            or current_cost_inventory() != inventory or code != _code()):
        raise ValueError('quantity_monitor_source_changed')
    _check_directories(value['source_directories'])
    observation = value['observation']
    if value.get('historical_exclusion_disposition') is not None:
        observation = _historical_exclusions(stage, observation,
            value['historical_exclusion_disposition'], coverage['input_manifest_sha256'])
    return {'issued': value['issued'], 'observation': observation}
