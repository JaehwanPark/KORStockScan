"""Read-only auxiliary reader preflight owned by release/startup automation.

Reuse native compatibility and registry validators before a policy is prepared
or a Main child starts. This never issues parity evidence or calls a provider.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.utils.constants import DATA_DIR


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify_bound_sources(receipt: dict) -> None:
    """Recheck the small, frozen dependency set without policy re-evaluation."""
    if (receipt.get('schema') != 'auxiliary_reader_readiness_v1'
            or receipt.get('status') not in {'pass', 'not_required'}
            or not isinstance(receipt.get('source_hashes'), dict)
            or (receipt.get('status') == 'pass' and not receipt['source_hashes'])):
        raise ValueError('auxiliary_reader_readiness_receipt_invalid')
    for name, expected in receipt['source_hashes'].items():
        path = Path(name)
        if not path.is_file() or _sha(path) != expected:
            raise ValueError('auxiliary_reader_readiness_source_changed:' + str(path))
    overlay = receipt.get('target_overlay')
    if overlay is not None:
        if (not isinstance(overlay, dict) or set(overlay) != {'path', 'sha256', 'artifact_content_sha256'}
                or not isinstance(overlay['path'], str)):
            raise ValueError('auxiliary_reader_readiness_overlay_receipt_invalid')
        path = Path(overlay['path'])
        if overlay['sha256'] is None and overlay['artifact_content_sha256'] is not None:
            raise ValueError('auxiliary_reader_readiness_overlay_receipt_invalid')
        if overlay['sha256'] is not None and (not isinstance(overlay['sha256'], str)
                or not isinstance(overlay['artifact_content_sha256'], str)):
            raise ValueError('auxiliary_reader_readiness_overlay_receipt_invalid')
        unchanged = (not path.exists() and not path.is_symlink() if overlay['sha256'] is None
                     else path.is_file() and not path.is_symlink() and _sha(path) == overlay['sha256'])
        if not unchanged:
            _verify_runtime_overlay_successor(receipt)


def _verify_runtime_overlay_successor(receipt):
    """Allow only a native same-day descendant after real machine activation."""
    from src.engine.scalping import mechanistic_entry_runtime_policy as native
    from src.engine.scalping import reversal_auxiliary_intraday as reader

    target_date = receipt['target_date']
    if datetime.now(ZoneInfo('Asia/Seoul')).date().isoformat() != target_date:
        raise ValueError('auxiliary_reader_readiness_overlay_changed')
    data = Path(receipt['data_root'])
    observed = receipt['target_overlay']
    expected_path = reader.root(data) / 'days' / target_date / (receipt['bundle_sha256'] + '.json')
    if Path(observed['path']) != expected_path or expected_path.is_symlink():
        raise ValueError('auxiliary_reader_readiness_overlay_path_invalid')
    active_pointer = native.root(data) / 'current.json'
    before = _sha(active_pointer)
    pointer = native._read(active_pointer)
    if (pointer.get('bundle_sha256') != receipt['bundle_sha256']
            or pointer.get('effective_date') != target_date):
        raise ValueError('auxiliary_reader_readiness_overlay_not_activated')
    bundle = native.load_effective(data_root=data, target_date=target_date)
    if not bundle or bundle.get('bundle_sha256') != receipt['bundle_sha256']:
        raise ValueError('auxiliary_reader_readiness_overlay_not_activated')
    current = reader.current(data, bundle, day=target_date)
    if current is None or reader.read(expected_path) != current:
        raise ValueError('auxiliary_reader_readiness_overlay_changed')
    record = current
    seen = set()
    expected = observed['artifact_content_sha256']
    found = False
    while record is not None:
        ident = record['artifact_content_sha256']
        if (ident in seen or record.get('day') != target_date
                or record.get('base_bundle_sha256') != receipt['bundle_sha256']):
            raise ValueError('auxiliary_reader_readiness_overlay_ancestry_invalid')
        seen.add(ident)
        generation = reader.root(data) / 'generations' / (ident + '.json')
        if reader.read(generation) != record:
            raise ValueError('auxiliary_reader_readiness_overlay_ancestry_invalid')
        reader.validate_record(data, record, bundle, check_definitions=True)
        evidenced = any(record.get(key) for key in ('evaluation_sha256', 'transition_manifest_sha256',
                                                    'contract_repair_manifest_sha256'))
        if not evidenced and not (record.get('rollback_reason') and record.get('previous_overlay_sha256')):
            raise ValueError('auxiliary_reader_readiness_overlay_publication_proof_missing')
        if ident == expected:
            found = True
            break
        previous = record.get('previous_overlay_sha256')
        if previous is None:
            found = expected is None
            break
        if not isinstance(previous, str) or re.fullmatch('[a-f0-9]{64}', previous) is None:
            raise ValueError('auxiliary_reader_readiness_overlay_ancestry_invalid')
        record = reader.read(reader.root(data) / 'generations' / (previous + '.json'))
        if record.get('artifact_content_sha256') != previous:
            raise ValueError('auxiliary_reader_readiness_overlay_ancestry_invalid')
    if (not found or _sha(active_pointer) != before
            or reader.current(data, bundle, day=target_date) != current
            or reader.read(expected_path) != current):
        raise ValueError('auxiliary_reader_readiness_overlay_changed')


def _registry_sources(data_root, registry, identities, sources):
    """Validate effective definitions and seal their immutable original parents."""
    pending = list(identities)
    visited = set()
    while pending:
        ident = pending.pop()
        if ident in visited:
            continue
        visited.add(ident)
        path = registry.directory(data_root) / (ident + '.json')
        actual = _sha(path)
        if sources.setdefault(str(path), actual) != actual:
            raise ValueError('auxiliary_reader_readiness_source_changed:' + str(path))
        value = registry.load(data_root, ident)
        for name in ('research_registry_sha256', 'production_parent_registry_sha256'):
            if value.get(name):
                pending.append(value[name])


def _runtime_overlay_generations(data_root, bundle, target_date, reader, overlay, sources):
    """Follow runtime ancestry explicitly; flat proof sources may be historical."""
    result = {}
    record = overlay
    while record is not None:
        ident = record.get('artifact_content_sha256')
        if (not isinstance(ident, str) or re.fullmatch('[a-f0-9]{64}', ident) is None
                or ident in result or record.get('day') != target_date
                or record.get('base_bundle_sha256') != bundle['bundle_sha256']
                or record.get('schema') != reader.SCHEMA or record.get('authority') != reader.AUTHORITY):
            raise ValueError('auxiliary_reader_readiness_overlay_ancestry_invalid')
        path = reader.root(data_root) / 'generations' / (ident + '.json')
        actual = _sha(path)
        if sources.setdefault(str(path), actual) != actual or reader.read(path) != record:
            raise ValueError('auxiliary_reader_readiness_overlay_ancestry_invalid')
        result[ident] = (path.resolve(), record)
        previous = record.get('previous_overlay_sha256')
        if previous is None:
            break
        if not isinstance(previous, str) or re.fullmatch('[a-f0-9]{64}', previous) is None:
            raise ValueError('auxiliary_reader_readiness_overlay_ancestry_invalid')
        record = reader.read(reader.root(data_root) / 'generations' / (previous + '.json'))
        if record.get('artifact_content_sha256') != previous:
            raise ValueError('auxiliary_reader_readiness_overlay_ancestry_invalid')
    return {path: value for path, value in result.values()}


def _target_overlay(data_root, bundle, target_date, reader, registry, inherited, sources):
    """Inspect the dated runtime overlay without registering or publishing it."""
    path = reader.root(data_root) / 'days' / target_date / (bundle['bundle_sha256'] + '.json')
    observed = dict(path=str(path), sha256=None, artifact_content_sha256=None)
    overlay = reader.current(data_root, bundle, day=target_date)
    if overlay is None:
        # A source may appear after the native read; never seal its absence then.
        if path.exists() or path.is_symlink():
            raise ValueError('auxiliary_reader_readiness_overlay_changed')
        _registry_sources(data_root, registry, inherited.values(), sources)
        return inherited, observed
    observed.update(sha256=_sha(path), artifact_content_sha256=overlay['artifact_content_sha256'])
    if reader.read(path) != overlay:
        raise ValueError('auxiliary_reader_readiness_overlay_changed')
    runtime_generations = _runtime_overlay_generations(
        data_root, bundle, target_date, reader, overlay, sources)
    lineage = reader.lineage_sources(data_root, bundle, overlay)
    for reference in lineage:
        previous = sources.setdefault(reference['path'], reference['sha256'])
        if previous != reference['sha256']:
            raise ValueError('auxiliary_reader_readiness_source_changed:' + reference['path'])
    for generation, record in runtime_generations.items():
        old = record.get('code_hashes')
        if old is not None and old != reader.code_hashes():
            from src.engine.scalping import reversal_auxiliary_compatibility as compatibility
            proof = compatibility.validate(data_root, bundle, generation, old, reader.code_hashes())
            proof_path = compatibility.path(data_root, bundle, generation, reader.code_hashes())
            for dependency in [proof_path, proof['evidence_path']] + [
                    item['path'] for item in proof['frozen_readers']]:
                name = str(dependency)
                actual = _sha(Path(dependency))
                if sources.setdefault(name, actual) != actual:
                    raise ValueError('auxiliary_reader_readiness_source_changed:' + name)
    bindings = {**inherited, **overlay['bindings']}
    identities = set(bindings.values()) | set(reader.rollback_bindings(data_root, bundle, overlay).values())
    _registry_sources(data_root, registry, identities, sources)
    # Seal before revalidation so mutations during validation remain observable.
    reader.validate_record(data_root, overlay, bundle, check_definitions=True)
    if reader.current(data_root, bundle, day=target_date) != overlay:
        raise ValueError('auxiliary_reader_readiness_overlay_changed')
    return bindings, observed


def verify_auxiliary_reader(
    target_date: str, *, data_root: Path = DATA_DIR, preparation: bool = False,
    bundle: dict | None = None,
) -> dict:
    from src.engine.scalping import mechanistic_entry_runtime_policy as native
    from src.engine.scalping import reversal_auxiliary_intraday as reader
    from src.engine.scalping import reversal_auxiliary_compatibility as compatibility
    from src.engine.scalping import reversal_auxiliary_registry as registry

    data_root = Path(data_root).resolve()
    if bundle is None:
        bundle = (native.load(data_root=data_root, target_date=target_date) if preparation
                  else native.load_effective(data_root=data_root, target_date=target_date))
    result = dict(schema='auxiliary_reader_readiness_v1', target_date=target_date,
                  phase='preparation' if preparation else 'runtime',
                  status='not_required', source_hashes={}, actual_pid_consumed=False,
                  provider_called=False, broker_called=False, order_submitted=False)
    family = (bundle or {}).get('continuous_reversal') or {}
    if family.get('schema') not in {'continuous_reversal_policy_v5', 'continuous_reversal_policy_v6'}:
        return result

    source = native.root(data_root) / 'sources' / ('reversal-' + family['auxiliary_report_sha256'] + '.json')
    report = reader.read(source)
    source_sha = _sha(source)
    if source_sha != family['report_file_sha256']['auxiliary']:
        raise ValueError('auxiliary_inherited_report_changed')
    refs = report.get('auxiliary_registry_bindings', {})
    if not isinstance(refs, dict):
        raise ValueError('auxiliary_inheritance_scope_invalid')
    if any(not isinstance(ident, str) or len(ident) != 64
           or any(c not in '0123456789abcdef' for c in ident) for ident in refs.values()):
        raise ValueError('auxiliary_registry_identity_invalid')
    current_hashes = reader.code_hashes()
    sources = {str(source): source_sha}
    sources.update({str(Path(reader.__file__).parent / name): sha
                    for name, sha in current_hashes.items()})
    sources.update({str(registry.directory(data_root) / (ident + '.json')):
                    _sha(registry.directory(data_root) / (ident + '.json'))
                    for ident in set(refs.values())})
    compatibility_path = None
    if refs and report.get('auxiliary_reader_code_hashes') != current_hashes:
        old_hashes = report.get('auxiliary_reader_code_hashes')
        if not isinstance(old_hashes, dict) or not old_hashes:
            raise ValueError('auxiliary_reader_code_hashes_invalid')
        # Validate directly, even when inherited() has a warm cached mapping.
        compatibility_path = compatibility.path(data_root, bundle, source, current_hashes)
        sources[str(compatibility_path)] = _sha(compatibility_path)
        receipt = compatibility.validate(data_root, bundle, source,
                                         old_hashes, current_hashes)
        sources[receipt['evidence_path']] = receipt['evidence_sha256']
        sources.update({item['path']: old_hashes[Path(item['path']).name]
                        for item in receipt['frozen_readers']})
    inherited = reader.inherited(data_root, bundle)
    if inherited != refs:
        raise ValueError('auxiliary_reader_inheritance_changed')
    effective, overlay = _target_overlay(data_root, bundle, target_date, reader, registry,
                                         inherited, sources)
    result.update(status='pass', bundle_sha256=bundle['bundle_sha256'],
                  auxiliary_source_path=str(source), auxiliary_source_sha256=source_sha,
                  reader_code_hashes=current_hashes, scope_count=len(effective),
                  target_overlay=overlay, data_root=str(data_root),
                  compatibility_path=str(compatibility_path) if compatibility_path else None,
                  compatibility_status='verified' if compatibility_path else 'not_required_same_readers',
                  source_hashes=sources)
    verify_bound_sources(result)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Verify auxiliary reader compatibility before Main startup.')
    parser.add_argument('--target-date', required=True)
    parser.add_argument('--data-root', type=Path, default=DATA_DIR)
    parser.add_argument('--preparation', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = verify_auxiliary_reader(args.target_date, data_root=args.data_root,
                                         preparation=args.preparation)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        result = dict(schema='auxiliary_reader_readiness_v1', status='fail',
                      target_date=args.target_date, findings=[type(exc).__name__ + ':' + str(exc)],
                      actual_pid_consumed=False, provider_called=False,
                      broker_called=False, order_submitted=False)
    print(json.dumps(result, sort_keys=True))
    return int(result['status'] == 'fail')


if __name__ == '__main__':
    raise SystemExit(main())
