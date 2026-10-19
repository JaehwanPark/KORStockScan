"""Content-bound dependencies of a cumulative Main holding report.

This lifecycle contract seals input generations, including missing dates. It
does not allocate costs or acquire policy/order authority. A legacy report
without the consumed window cannot be made current by resealing its bytes.
"""
from __future__ import annotations

from datetime import date, timedelta
from contextlib import ExitStack
import gzip
import hashlib
import json
import io
from functools import lru_cache
from pathlib import Path

from .broker_cost_reconciliation import digest, source_generation

SCHEMA = "holding_input_window_generation_v1"
MAX_DATES = 370
MAX_PROJECTION_BYTES = 4 * 1024 * 1024
MAX_METADATA_BYTES = 512 * 1024


def source_stat(stat):
    """Access time changes when this verifier reads; it is not source mutation."""
    return tuple(getattr(stat, key) for key in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))


def byte_generation(path):
    """Independent byte verification, with a constant 64 KiB read buffer."""
    path = Path(path)
    if (path.parent.name == 'monitor_snapshots' and path.name.endswith(('.json', '.json.gz'))
            and not (path.name.endswith('.gz') and not Path(str(path)+'.archive_receipt.json').exists())):
        from .snapshot_archive import generation
        return generation(path)
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise ValueError('window_dependency_path_invalid')
    before = path.stat()
    from src.engine.infrastructure.validation_digest_session import reused_digest
    reused = reused_digest(path)
    if reused is not None:
        if source_stat(path.stat()) != source_stat(before):
            raise ValueError('window_dependency_changed_during_read')
        return {'path': path.name, 'size': before.st_size, 'sha256': reused}
    sha = hashlib.sha256()
    size = 0
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(64 * 1024), b''):
            size += len(block)
            sha.update(block)
    if source_stat(path.stat()) != source_stat(before) or size != before.st_size:
        raise ValueError('window_dependency_changed_during_read')
    return {'path': path.name, 'size': size, 'sha256': sha.hexdigest()}


@lru_cache(maxsize=128)
def _code_file_generation(name, stat):
    path = Path(name)
    value = byte_generation(path)['sha256']
    if source_stat(path.stat()) != stat:
        raise ValueError('code_generation_changed_during_read')
    return value


@lru_cache(maxsize=16)
def _code_generation(signature):
    return tuple((name, _code_file_generation(name, stat)) for name, stat in signature)


def cached_code_generation(paths):
    """Bounded code-only cache; source/cost receipts remain independently read."""
    paths = tuple(Path(path) for path in paths)
    if any(p.is_symlink() or any(parent.is_symlink() for parent in p.parents) for p in paths):
        raise ValueError('code_generation_path_invalid')
    signature = tuple((str(p), source_stat(p.stat())) for p in paths)
    value = dict(_code_generation(signature))
    if signature != tuple((str(p), source_stat(p.stat())) for p in paths):
        raise ValueError('code_generation_changed_during_read')
    return value


def seal_dependency_receipt(sidecar, payload, *, fact_projection=None,
                            projection_generation=None,trailing_completed_index=None):
    """Only the existing, census-verified projection writer calls this."""
    from src.engine.sniper_trade_review_report import verify_completed_census_manifest
    from src.engine.scalping.pre_submit_delay_initial_policy import _atomic
    if verify_completed_census_manifest(payload, payload['date']) is not None:
        raise ValueError('window_dependency_census_invalid')
    if projection_generation is not None:
        from src.engine.infrastructure.validation_digest_session import _native_bytes
        proof=_native_bytes(Path(sidecar).parent.parent.parent,sidecar)
        if proof is None or proof['generation']!=projection_generation:
            raise ValueError('window_dependency_native_writer_proof_missing')
    observed_projection=projection_generation or byte_generation(sidecar)
    if projection_generation is None and (Path(sidecar).parent.name=='monitor_snapshots'
            and Path(sidecar).parent.parent.name=='report'):
        # Legacy native producers may explicitly seal a fully read generation.
        # This is a writer action, never an inline consumer repair.
        from src.engine.infrastructure.validation_digest_session import publish_native_bytes
        publish_native_bytes(Path(sidecar).parent.parent.parent,sidecar,observed_projection)
    body = {'schema':'holding_projection_dependency_receipt_v1', 'date':payload['date'],
            'projection':observed_projection, 'snapshot_identity':payload['snapshot_identity'],
            'census_sha256':digest(payload['meta']['completed_census_manifest']),
            'meta':{k:payload['meta'].get(k) for k in (
                'actual_cost_source_generation', 'knowledge_cutoff', 'snapshot_profile')},
            'completed_count':len(payload['sections']['completed_trade_projection'])}
    if fact_projection is not None:
        body['fact_projection'] = byte_generation(fact_projection)
    if trailing_completed_index is not None:
        body['trailing_completed_index']=trailing_completed_index
    body['artifact_sha256'] = digest(body)
    if len(json.dumps(body).encode()) > MAX_METADATA_BYTES:
        raise ValueError('window_dependency_metadata_budget_exceeded')
    _atomic(Path(str(sidecar) + '.dependencies.json'), body)


def _file_generation(path: Path) -> dict:
    if path.parent.name == 'monitor_snapshots' and path.suffix == '.json':
        from .snapshot_archive import generation, read_bytes
        observed = generation(path)
        if observed['size'] > MAX_PROJECTION_BYTES:
            raise ValueError('window_dependency_projection_unbounded')
        raw = read_bytes(path, maximum=MAX_PROJECTION_BYTES)
        if len(raw) != observed['size'] or hashlib.sha256(raw).hexdigest() != observed['sha256']:
            raise ValueError('window_dependency_changed_during_read')
        return observed, raw
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise ValueError("window_dependency_path_invalid")
    before = path.stat()
    if before.st_size > MAX_PROJECTION_BYTES:
        raise ValueError("window_dependency_projection_unbounded")
    with path.open("rb") as handle:
        raw = handle.read(MAX_PROJECTION_BYTES + 1)
    after = path.stat()
    if len(raw) > MAX_PROJECTION_BYTES or source_stat(before) != source_stat(after):
        raise ValueError("window_dependency_changed_during_read")
    return {"path": path.name, "size": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}, raw


def _capture_day(root, directory, day):
    with ExitStack() as budget:
        return _capture_day_inputs(root, directory, day, budget)


def completed_projection_census_issue(value, day, *, costs):
    """Preserve the original empty census predating an optional unknown cost key."""
    from src.engine.sniper_trade_review_report import verify_completed_census_manifest, completed_census_manifest
    try:
        issue = verify_completed_census_manifest(value, day)
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
        return 'completed_census_contract_invalid'
    if issue is None:
        return None
    if issue != 'completed_census_generation_mismatch':
        return issue
    meta = value.get('meta')
    metrics = value.get('metrics')
    census = meta.get('completed_census_manifest') if isinstance(meta, dict) else None
    if (not isinstance(census, dict) or meta.get('snapshot_profile') != 'postclose_exit'
            or 'actual_cost_source_generation' in meta or 'actual_cost_source_generation' in census
            or census.get('source_receipts_status') != 'structured_projection_receipts_observed'
            or type(costs.get('count')) is not int or costs['count'] != 0 or costs.get('official_source_sha256')
            or not isinstance(metrics, dict) or type(metrics.get('canonical_completed_trades')) is not int
            or metrics['canonical_completed_trades'] != 0
            or any(key in meta and (type(meta[key]) is not int or meta[key] != 0) for key in (
                'completion_event_id_count','completion_event_unresolved_id_count'))
            or (value.get('sections') or {}).get('completed_trade_projection') != []
            or any(type(census.get(key)) is not int or census[key] != 0 for key in (
                'raw_terminal_count','raw_completion_event_count','projected_count','valid_profit_count',
                'strict_count','excluded_count','unobserved_count'))):
        return issue
    expected = completed_census_manifest(value)
    if 'actual_cost_source_generation' not in expected or expected.pop('actual_cost_source_generation') is not None:
        return issue
    return None if expected == census else issue


def verified_archived_empty_projection(data_root, day):
    """Consume current native gzip bytes for an original empty postclose.

    No formerly existing inode or archive receipt is inferred. Nonempty
    completions keep their stricter identity and retained-proof contracts.
    """
    import os
    import stat
    import zlib
    from datetime import datetime
    from .research_input_budget import Claim
    from src.engine.strategy_position_performance_report import _legacy_source_json
    root = Path(data_root).resolve()
    logical = root/'report/monitor_snapshots'/f'trade_review_{day}.json'
    physical = Path(str(logical)+'.gz')
    archive_receipt = Path(str(physical)+'.archive_receipt.json')
    manifest = logical.parent/'manifests'/f'monitor_snapshot_manifest_{day}_postclose_exit.json'
    paths = (logical, physical, archive_receipt, manifest)
    def signature():
        return tuple((str(p), source_stat(p.lstat()) if p.exists() or p.is_symlink() else None) for p in paths)
    before = signature()
    if logical.exists() or logical.is_symlink() or archive_receipt.exists() or archive_receipt.is_symlink():
        raise ValueError('window_archived_empty_not_applicable')
    if physical.is_symlink() or any(p.is_symlink() for p in physical.parents):
        raise ValueError('window_archived_empty_path_invalid')
    observed = physical.lstat()
    if not stat.S_ISREG(observed.st_mode) or observed.st_size > MAX_PROJECTION_BYTES:
        raise ValueError('window_archived_empty_size_or_type_invalid')
    with ExitStack() as budget:
        budget.enter_context(Claim(observed.st_size + MAX_PROJECTION_BYTES + 1))
        fd = os.open(physical, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            if source_stat(os.fstat(fd)) != source_stat(observed):
                raise ValueError('window_archived_empty_changed')
            with os.fdopen(fd, 'rb', closefd=False) as handle:
                compressed = handle.read(MAX_PROJECTION_BYTES + 1)
            if (len(compressed) != observed.st_size or source_stat(os.fstat(fd)) != source_stat(observed)):
                raise ValueError('window_archived_empty_changed')
        finally:
            os.close(fd)
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as decoded:
                content = decoded.read(MAX_PROJECTION_BYTES + 1)
            if len(content) > MAX_PROJECTION_BYTES:
                raise ValueError('window_archived_empty_decoded_unbounded')
        except (EOFError, gzip.BadGzipFile, zlib.error) as exc:
            raise ValueError('window_archived_empty_compression_invalid') from exc
        budget.enter_context(Claim(len(content) * 8))
        def unique_pairs(pairs):
            result = {}
            for key, item in pairs:
                if key in result:
                    raise ValueError('window_archived_empty_duplicate_key')
                result[key] = item
            return result
        try:
            value = json.loads(content, object_pairs_hook=unique_pairs)
        except RecursionError as exc:
            raise ValueError('window_archived_empty_contract_invalid') from exc
        if not isinstance(value, dict) or not isinstance(value.get('meta'), dict):
            raise ValueError('window_archived_empty_contract_invalid')
        meta = value['meta']
        if meta.get('snapshot_profile') != 'postclose_exit':
            raise ValueError('window_archived_empty_not_applicable')
        census = meta.get('completed_census_manifest')
        sections = value.get('sections')
        metrics = value.get('metrics')
        costs = source_generation(root, day)
        recorded = meta.get('actual_cost_source_generation')
        if (value.get('date') != day or value.get('scope') != 'entered' or value.get('code') or value.get('since')
                or meta.get('warnings') or not isinstance(census, dict)
                or not isinstance(sections,dict) or not isinstance(metrics,dict)
                or census.get('source_receipts_status') != 'structured_projection_receipts_observed'
                or meta.get('sell_completed_event_ids') != []
                or any(key in meta and (type(meta[key]) is not int or meta[key] != 0) for key in (
                    'completion_event_id_count','completion_event_unresolved_id_count'))
                or any(type(census.get(key)) is not int or census[key] != 0 for key in (
                    'raw_terminal_count','raw_completion_event_count','projected_count','valid_profit_count',
                    'strict_count','excluded_count','unobserved_count'))
                or sections.get('completed_trade_projection') != []
                or type(metrics.get('canonical_completed_trades')) is not int
                or metrics['canonical_completed_trades'] != 0
                or recorded is not None and (not isinstance(recorded, dict) or type(recorded.get('count')) is not int)
                or recorded != costs and (recorded is not None or costs['count'] or costs.get('official_source_sha256'))
                or completed_projection_census_issue(value, day, costs=costs) is not None):
            raise ValueError('window_archived_empty_contract_invalid')
        body, manifest_bytes = _legacy_source_json(manifest, MAX_METADATA_BYTES)
        try:
            generated = datetime.strptime(body.get('generated_at'), '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError) as exc:
            raise ValueError('window_archived_empty_manifest_invalid') from exc
        kinds = {'trade_review','post_sell_feedback','holding_exit_observation','missed_entry_counterfactual'}
        declared_kinds = body.get('snapshot_kinds')
        expected_paths = {kind:str(logical.parent/f'{kind}_{day}.json') for kind in kinds}
        hashes = body.get('snapshot_sha256')
        logical_sha = hashlib.sha256(content).hexdigest()
        base_fields = {'target_date','profile','generated_at','snapshot_kinds','snapshot_paths','snapshot_sha256'}
        window_fields = {'actual_cost_source_generation','input_window_dependencies','input_window_generation_sha256'}
        if (set(body) not in (base_fields, base_fields | window_fields)
                or body.get('target_date') != day or body.get('profile') != 'postclose_exit'
                or generated.strftime('%Y-%m-%d %H:%M:%S') != body['generated_at']
                or generated.date().isoformat() < day
                or not isinstance(declared_kinds,list) or len(declared_kinds) != len(kinds)
                or any(not isinstance(k,str) for k in declared_kinds) or set(declared_kinds) != kinds
                or body.get('snapshot_paths') != expected_paths or not isinstance(hashes,dict) or set(hashes) != kinds
                or any(not isinstance(sha,str) or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha)
                       for sha in hashes.values()) or hashes['trade_review'] != logical_sha):
            raise ValueError('window_archived_empty_manifest_invalid')
        historical_window = body.get('input_window_dependencies')
        if set(body) == base_fields | window_fields:
            # This is the original producer's internally sealed window, not a
            # request to replay its old dependencies against today's sources.
            if (not isinstance(historical_window, dict)
                    or set(historical_window) != {'schema','data_root','dates','dependencies','input_window_generation_sha256'}
                    or historical_window.get('schema') != SCHEMA
                    or historical_window.get('data_root') != str(root)
                    or not isinstance(body['actual_cost_source_generation'], dict)
                    or type(body['actual_cost_source_generation'].get('count')) is not int
                    or body['actual_cost_source_generation'] != costs or recorded != costs):
                raise ValueError('window_archived_empty_manifest_window_invalid')
            dates = historical_window.get('dates')
            dependencies = historical_window.get('dependencies')
            try:
                if (not isinstance(dates, list) or not dates or len(dates) > MAX_DATES
                        or any(not isinstance(item, str) for item in dates)):
                    raise ValueError('invalid_dates')
                parsed = [date.fromisoformat(item) for item in dates]
                if (dates != sorted(set(dates)) or dates[-1] != day
                        or any(item.isoformat() != text for item, text in zip(parsed, dates))
                        or any(right-left != timedelta(days=1) for left, right in zip(parsed, parsed[1:]))):
                    raise ValueError('invalid_dates')
            except (ValueError, TypeError) as exc:
                raise ValueError('window_archived_empty_manifest_window_invalid') from exc
            source = dependencies.get(day) if isinstance(dependencies, dict) else None
            if (not isinstance(dependencies, dict) or set(dependencies) != set(dates)
                    or any(not isinstance(item, dict) for item in dependencies.values())
                    or not isinstance(source, dict)
                    or set(source) != {'status','projection','census_sha256','cost_generation','profile','knowledge_cutoff'}
                    or source['status'] != 'valid_empty' or not isinstance(source['projection'], dict)
                    or not isinstance(source['cost_generation'], dict)
                    or type(source['cost_generation'].get('count')) is not int
                    or source['cost_generation'] != costs or source['census_sha256'] != digest(census)
                    or source['profile'] != meta['snapshot_profile']
                    or source['knowledge_cutoff'] != meta.get('knowledge_cutoff')
                    or digest({k:v for k,v in historical_window.items() if k != 'input_window_generation_sha256'})
                        != historical_window['input_window_generation_sha256']
                    or body['input_window_generation_sha256'] != historical_window['input_window_generation_sha256']):
                raise ValueError('window_archived_empty_manifest_window_invalid')
        if signature() != before or source_generation(root,day) != costs:
            raise ValueError('window_archived_empty_changed')
        generation = dict(path=physical.name,size=len(compressed),sha256=hashlib.sha256(compressed).hexdigest(),
            logical_size=len(content),logical_content_sha256=logical_sha,
            physical_generation=dict(zip(('device','inode','size','mtime_ns','ctime_ns'),source_stat(observed))),
            original_native_manifest=dict(path=manifest.name,size=len(manifest_bytes),sha256=hashlib.sha256(manifest_bytes).hexdigest()),
            source_basis='current_native_gzip_empty_postclose')
        if historical_window is not None:
            generation['original_input_window'] = {
                'input_window_generation_sha256': historical_window['input_window_generation_sha256'],
                'dates': historical_window['dates'],
                'validation_basis': 'original_manifest_internal_seal_and_source_day_binding'}
        return value, generation


def verified_legacy_projection_dependency(data_root, day, *, projection_generation=None):
    from .research_input_budget import Claim
    with Claim((MAX_METADATA_BYTES + 1) * 8):
        return _verified_legacy_projection_dependency(data_root, day,
            projection_generation=projection_generation)


def _verified_legacy_projection_dependency(data_root, day, *, projection_generation=None):
    """Read original metadata through its retained, fully verified native proof.

    This is a native source consumer, not a replacement for full byte/census
    validation. The original large projection and any original receipts remain
    unchanged. A fact-only scalar projection never supplies holding paths.
    """
    import codecs
    import os
    import stat
    from src.engine.strategy_position_performance_report import _legacy_original_generation_issue, _legacy_source_json
    from .snapshot_archive import snapshot_identity, snapshot_identity_matches
    root = Path(data_root).resolve()
    directory = root / 'report/monitor_snapshots'
    raw = directory / f'trade_review_{day}.json'
    sidecar = raw.with_suffix('.completed_projection.json')
    proof = {}
    legacy, issue = _legacy_original_generation_issue(day, data_dir=root, validated_proof=proof)
    if not legacy or issue:
        raise ValueError(issue or 'window_dependency_legacy_metadata_required')
    kind = proof.get('projection_kind', 'completed_sidecar')
    if kind not in {'completed_sidecar', 'original_snapshot'}:
        raise ValueError('window_dependency_legacy_projection_kind_invalid')
    projection = sidecar if kind == 'completed_sidecar' else raw
    if proof['projection']['path'] != str(projection):
        raise ValueError('window_dependency_legacy_original_generation_changed')
    proof_path = root/'report/strategy_position_fact_sync/legacy_sources'/day/(proof['artifact_sha256']+'.json')
    status_path = root/'report/strategy_position_fact_sync'/f'strategy_position_fact_sync_{day}.status.json'
    paths = [proof_path, status_path] + [p for logical in (raw, sidecar) for p in
        (logical, Path(str(logical)+'.gz'), Path(str(logical)+'.gz.archive_receipt.json'))]
    original_manifest = proof.get('original_snapshot_manifest')
    if original_manifest is not None:
        paths.append(Path(original_manifest['path']))
    def signature():
        return tuple((str(p), source_stat(p.lstat()) if p.exists() or p.is_symlink() else None) for p in paths)
    before = signature()
    generation = projection_generation or byte_generation(projection)
    expected = proof['projection']
    if (generation != dict(path=projection.name, size=expected['identity']['size'], sha256=expected['sha256'])
            or not snapshot_identity_matches(raw, proof['snapshot']['identity'], expected_sha256=proof['snapshot']['sha256'])):
        raise ValueError('window_dependency_legacy_original_generation_changed')
    # Native snapshots put the metadata before the large section. Bound this
    # read independently; a different layout needs an explicit partition.
    physical = projection if projection.exists() else Path(str(projection)+'.gz')
    if physical.is_symlink() or any(p.is_symlink() for p in physical.parents):
        raise ValueError('window_dependency_legacy_metadata_path_invalid')
    observed = physical.lstat()
    if not stat.S_ISREG(observed.st_mode):
        raise ValueError('window_dependency_legacy_metadata_path_invalid')
    fd = os.open(physical, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        if source_stat(os.fstat(fd)) != source_stat(observed):
            raise ValueError('window_dependency_legacy_metadata_changed')
        with os.fdopen(fd, 'rb', closefd=False) as handle:
            stream = gzip.GzipFile(fileobj=handle) if physical.suffix == '.gz' else handle
            try:
                prefix = stream.read(MAX_METADATA_BYTES + 1)
            finally:
                if stream is not handle:
                    stream.close()
        if source_stat(os.fstat(fd)) != source_stat(observed):
            raise ValueError('window_dependency_legacy_metadata_changed')
    finally:
        os.close(fd)
    text = codecs.getincrementaldecoder('utf-8')().decode(prefix, final=False)
    decoder = json.JSONDecoder()
    index = 0
    def space():
        nonlocal index
        while index < len(text) and text[index].isspace():
            index += 1
    space()
    if text[index:index+1] != '{':
        raise ValueError('window_dependency_legacy_metadata_invalid')
    index += 1
    metadata = None
    try:
        for _ in range(256):
            space(); key, index = decoder.raw_decode(text, index); space()
            if not isinstance(key, str) or text[index:index+1] != ':':
                raise ValueError('window_dependency_legacy_metadata_invalid')
            index += 1; space(); value, index = decoder.raw_decode(text, index)
            if key == 'meta':
                metadata = value
                break
            space()
            if text[index:index+1] != ',':
                break
            index += 1
    except (ValueError, RecursionError) as exc:
        raise ValueError('window_dependency_legacy_metadata_partition_required') from exc
    scalar_meta = proof['scalar_projection']['meta']
    if (not isinstance(metadata, dict) or metadata.get('snapshot_profile') != 'postclose_exit'
            or metadata.get('completed_census_manifest') != scalar_meta['completed_census_manifest']
            or metadata.get('actual_cost_source_generation') != proof['original_actual_cost_source_generation']
            or ('actual_cost_source_generation' in metadata) != proof['original_actual_cost_generation_field_present']):
        raise ValueError('window_dependency_legacy_metadata_binding_invalid')
    final_proof = {}
    legacy, issue = _legacy_original_generation_issue(day, data_dir=root, validated_proof=final_proof)
    if not legacy or issue or final_proof != proof or signature() != before:
        raise ValueError(issue or 'window_dependency_legacy_metadata_changed')
    census = metadata['completed_census_manifest']
    value = dict(schema='holding_retained_original_projection_dependency_v1', date=day,
        snapshot_identity=proof['snapshot']['identity'], meta=metadata,
        census_sha256=digest(census), completed_count=census['projected_count'],
        observed_actual_cost_source_generation=proof['observed_actual_cost_source_generation'])
    if original_manifest is not None:
        value['original_snapshot_manifest'] = original_manifest
    proof_body, proof_bytes = _legacy_source_json(proof_path, MAX_METADATA_BYTES)
    _, status_bytes = _legacy_source_json(status_path, MAX_METADATA_BYTES)
    if proof_body != proof:
        raise ValueError('window_dependency_legacy_metadata_changed')
    def bounded_generation(path, content):
        return dict(path=path.name, size=len(content), sha256=hashlib.sha256(content).hexdigest())
    generation = {**generation, 'legacy_validation':dict(
        proof=bounded_generation(proof_path, proof_bytes), status=bounded_generation(status_path, status_bytes))}
    if original_manifest is not None:
        generation['legacy_validation']['original_snapshot_manifest'] = original_manifest
    if signature() != before:
        raise ValueError('window_dependency_legacy_metadata_changed')
    return value, generation


def _capture_day_inputs(root, directory, day, budget):
    from .research_input_budget import Claim
    def decode(content):
        budget.enter_context(Claim(len(content) * 8))
        return json.loads(content)
    raw = directory / f"trade_review_{day}.json"
    compressed = Path(str(raw) + ".gz")
    sidecar = raw.with_suffix(".completed_projection.json")
    # The bounded sidecar is authoritative only with its original snapshot
    # identity. Preserve that binding as well as the sidecar's bytes.
    from .snapshot_archive import present, snapshot_identity, identity_available, snapshot_identity_matches
    if identity_available(raw) and present(sidecar):
        receipt = Path(str(sidecar) + '.dependencies.json')
        if receipt.is_file():
            if receipt.stat().st_size > MAX_METADATA_BYTES:
                raise ValueError('window_dependency_metadata_budget_exceeded')
            receipt_generation, content = _file_generation(receipt)
            metadata = decode(content)
            generation = byte_generation(sidecar)
            if (metadata.get('schema') != 'holding_projection_dependency_receipt_v1'
                    or metadata.get('date') != day or metadata.get('projection') != generation
                    or metadata.get('artifact_sha256') != digest({k:v for k,v in metadata.items() if k != 'artifact_sha256'})
                    or type(metadata.get('completed_count')) is not int or metadata['completed_count'] < 0):
                raise ValueError('window_dependency_receipt_invalid')
            generation['dependency_receipt'] = receipt_generation
            value = metadata
        else:
            # Legacy projections remain verifiable when small. Large historical
            # files require the existing producer's receipt, not an unbounded
            # JSON decode or a fabricated validation marker.
            generation = byte_generation(sidecar)
            if generation['size'] > MAX_PROJECTION_BYTES:
                value, generation = verified_legacy_projection_dependency(root, day, projection_generation=generation)
            else:
                generation, content = _file_generation(sidecar)
                value = decode(content)
        identity = snapshot_identity(raw)
        if raw.is_symlink() or ('legacy_validation' not in generation
                and not snapshot_identity_matches(raw, value.get("snapshot_identity"))):
            raise ValueError("window_dependency_snapshot_binding_invalid")
        generation["snapshot_identity"] = value["snapshot_identity"]
        if not receipt.is_file() and 'legacy_validation' not in generation:
            payload = {k: v for k, v in value.items() if k != 'artifact_sha256'}
            expected = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'),
                                                ensure_ascii=False).encode()).hexdigest()
            if (value.get('schema') != 'trade_review_completed_projection_sidecar_v1'
                    or expected != value.get('artifact_sha256')
                    or completed_projection_census_issue(value, day, costs=source_generation(root,day)) is not None):
                raise ValueError('window_dependency_projection_contract_invalid')
    elif raw.is_file() or compressed.is_file():
        path = raw if raw.is_file() or Path(str(compressed)+'.archive_receipt.json').is_file() else compressed
        archived_empty = False
        if path.suffix == '.gz':
            try:
                value, generation = verified_archived_empty_projection(root, day)
                budget.enter_context(Claim(generation['logical_size'] * 8))
                archived_empty = True
            except ValueError as exc:
                if str(exc) != 'window_archived_empty_not_applicable':
                    raise
        if not archived_empty:
            generation = byte_generation(path)
            if generation['size'] > MAX_PROJECTION_BYTES and path == raw:
                value, generation = verified_legacy_projection_dependency(root, day, projection_generation=generation)
            else:
                generation, content = _file_generation(path)
                if path.suffix == '.gz':
                    with gzip.GzipFile(fileobj=io.BytesIO(content)) as handle:
                        content = handle.read(MAX_PROJECTION_BYTES + 1)
                if len(content) > MAX_PROJECTION_BYTES:
                    raise ValueError("window_dependency_decoded_projection_unbounded")
                value = decode(content)
    else:
        generation, value = None, None
    costs = source_generation(root, day)
    status = "missing"
    census = None
    cutoff = None
    profile = None
    if value is not None:
        if value.get("date") != day:
            raise ValueError("window_dependency_snapshot_date_invalid")
        meta = value.get("meta") or {}
        recorded = meta.get("actual_cost_source_generation")
        if recorded != costs and (recorded is not None or costs["count"]
                                  or costs.get("official_source_sha256")):
            raise ValueError("window_dependency_cost_generation_changed:" + day)
        census = meta.get("completed_census_manifest")
        cutoff = meta.get("knowledge_cutoff")
        profile = meta.get("snapshot_profile")
        census_sha = value.get('census_sha256') or (digest(census) if census else None)
        status = "observed" if (value.get('completed_count', 0) > 0 or (value.get("sections") or {}).get(
            "completed_trade_projection")) else "valid_empty" if census_sha else "unverified"
    return {"status": status, "projection": generation,
            "census_sha256": (value.get('census_sha256') or (digest(census) if census else None)) if value else None,
            "cost_generation": costs, "profile": profile,
            "knowledge_cutoff": cutoff}


def capture_window(data_root: Path, dates: list[str]) -> dict:
    if not dates or len(dates) > MAX_DATES or dates != sorted(set(dates)):
        raise ValueError("window_dependency_dates_invalid")
    parsed = [date.fromisoformat(day) for day in dates]
    if any(day.isoformat() != text for day, text in zip(parsed, dates)) or any(
        right - left != timedelta(days=1) for left, right in zip(parsed, parsed[1:])
    ):
        raise ValueError("window_dependency_dates_invalid")
    root = Path(data_root).resolve()
    directory = root / "report/monitor_snapshots"
    rows = {}
    for day in dates:
        try:
            rows[day] = _capture_day(root, directory, day)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            # The date is identifiable. Isolate it and retain its generation;
            # an invalid old row cannot erase valid current analysis.
            projections = {}
            for path in directory.glob(f'trade_review_{day}*'):
                if path.name.endswith('.archive_receipt.json'):
                    continue
                from .snapshot_archive import logical_path, snapshot_identity
                if path.name.endswith('.json.gz') and Path(str(path)+'.archive_receipt.json').is_file():
                    logical = logical_path(path)
                    try:
                        identity = snapshot_identity(logical)
                        projections[logical.name] = byte_generation(logical) if identity['size'] <= MAX_PROJECTION_BYTES else {
                            **identity, 'status':'unverified_unbounded_source'}
                    except (OSError,ValueError,KeyError,TypeError):
                        # Keep this identifiable corrupt date isolated. A bad
                        # receipt must not escape the source-gap recovery path.
                        for physical in (path,Path(str(path)+'.archive_receipt.json')):
                            stat=physical.lstat()
                            projections[physical.name] = dict(size=stat.st_size,mtime_ns=stat.st_mtime_ns,
                                ctime_ns=stat.st_ctime_ns,inode=stat.st_ino,device=stat.st_dev,
                                status='unverified_archive_generation')
                    continue
                if path.is_file() and not path.is_symlink():
                    stat = path.stat()
                    projections[path.name] = byte_generation(path) if stat.st_size <= MAX_PROJECTION_BYTES else {
                        'size':stat.st_size, 'mtime_ns':stat.st_mtime_ns, 'ctime_ns':stat.st_ctime_ns,
                        'inode':stat.st_ino, 'device':stat.st_dev, 'status':'unverified_unbounded_source'}
            rows[day] = {'status':'source_gap', 'reason':str(exc), 'projection':projections,
                         'census_sha256':None, 'cost_generation':source_generation(root, day),
                         'profile':None, 'knowledge_cutoff':None}
    body = {"schema": SCHEMA, "data_root": str(root), "dates": dates,
            "dependencies": rows}
    return {**body, "input_window_generation_sha256": digest(body)}


def verify_window(data_root: Path, recorded: dict) -> None:
    if not isinstance(recorded, dict) or recorded.get("schema") != SCHEMA:
        raise ValueError("window_dependency_unverified")
    body = {key: value for key, value in recorded.items()
            if key != "input_window_generation_sha256"}
    if digest(body) != recorded.get("input_window_generation_sha256"):
        raise ValueError("window_dependency_hash_invalid")
    if capture_window(data_root, recorded.get("dates")) != recorded:
        raise ValueError("window_dependency_generation_changed")
