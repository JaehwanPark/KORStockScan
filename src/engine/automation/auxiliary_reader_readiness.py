"""Read-only auxiliary reader preflight owned by release/startup automation.

Reuse native compatibility and registry validators before a policy is prepared
or a Main child starts. This never issues parity evidence or calls a provider.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

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


def verify_auxiliary_reader(
    target_date: str, *, data_root: Path = DATA_DIR, preparation: bool = False,
    bundle: dict | None = None,
) -> dict:
    from src.engine.scalping import mechanistic_entry_runtime_policy as native
    from src.engine.scalping import reversal_auxiliary_intraday as reader
    from src.engine.scalping import reversal_auxiliary_compatibility as compatibility
    from src.engine.scalping import reversal_auxiliary_registry as registry

    data_root = Path(data_root)
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
    result.update(status='pass', bundle_sha256=bundle['bundle_sha256'],
                  auxiliary_source_path=str(source), auxiliary_source_sha256=source_sha,
                  reader_code_hashes=current_hashes, scope_count=len(inherited),
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
