"""Optional postclose sidecar for one frozen Samsung candidate, without publishing.

Ownership: offline postclose automation, not a trading stage or startup gate.
Missing sources create a sealed waiting receipt. An unchanged input generation
is reused; a newly available predecessor creates a new immutable generation.
"""
from __future__ import annotations

import argparse
import fcntl
import json
from datetime import date
from pathlib import Path

from src.engine.scalping import samsung_tick_transition_forward_validation as consumer
from src.utils.jsonl_io import write_json_object_generation_safe as atomic_write_json


CONTRACT_PATH = 'data/runtime/research/samsung_tick_transition/consumer-contract-v2.json'
REPORT_DIR = 'data/report/samsung_tick_transition_forward_validation'


def _report_folder(root: Path, day: str) -> Path:
    # Immutable releases share the workspace data directory. Resolve this
    # mount alias only; the generation writer still rejects symlinks below it.
    return (root / 'data').resolve() / Path(REPORT_DIR).relative_to('data') / day


def run(root: Path, day: str, *, contract_path: Path | None = None):
    root = root.resolve()
    if date.fromisoformat(day).isoformat() != day or day < '2026-10-06':
        raise ValueError('samsung_sidecar_requires_forward_source_date')
    folder = _report_folder(root, day)
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / 'run.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return dict(source_date=day, status='running', generation=None, result_path=None)
        try:
            return _run_locked(root, day, folder, contract_path)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            _failure(root, day, exc)
            raise


def _run_locked(root, day, folder, contract_path):
    contract_path = contract_path or root / CONTRACT_PATH
    if not contract_path.is_file() or contract_path.is_symlink():
        raise ValueError('samsung_sidecar_consumer_contract_missing_or_untrusted')
    contract = consumer.read(contract_path)
    consumer.validate_registration(root, contract)
    contract_sha = consumer.H.file_sha(contract_path)
    paths = consumer.source_paths(root, day)
    sources = {key: {'path': str(path), 'sha256': consumer.H.file_sha(path)
                     if path.is_file() and not path.is_symlink() else None}
               for key, path in paths.items()}
    if any(path.is_symlink() for path in paths.values()):
        raise ValueError('samsung_sidecar_source_symlink')
    identity = {'source_date': day, 'contract_file_sha256': contract_sha,
                'adapter_sha256': consumer.H.file_sha(__file__), 'sources': sources}
    generation = consumer.S.digest(identity)
    output = folder / generation
    if output.exists():
        result = consumer.read(output / 'result.json')
        if (result != consumer.A.seal(result) or result.get('day') != day
            or result.get('consumer_contract_sha256') != contract['artifact_content_sha256']):
            raise ValueError('samsung_sidecar_existing_generation_invalid')
        # Validate all successful input seals on reuse, including shards and
        # policy generations beyond the three top-level predecessor files.
        consumer.C.verify_seals(result.get('source_seals') or {})
    else:
        result = consumer.prepare(root, day, contract, output)
    if consumer.H.file_sha(contract_path) != contract_sha or any(
        value['sha256'] != (consumer.H.file_sha(paths[key]) if paths[key].is_file() else None)
        for key, value in sources.items()):
        raise ValueError('samsung_sidecar_source_generation_changed')
    index = consumer.A.seal(dict(schema='samsung_frozen_postclose_index_v1',
        owner='SamsungFrozenCandidateValidation1006', source_date=day,
        target_date=None, generation=generation, identity=identity,
        status=result['status'], result_path=str(output / 'result.json'),
        result_file_sha256=consumer.H.file_sha(output / 'result.json'),
        candidate_id=consumer.CANDIDATE, runtime_effect=False,
        actual_order_submitted=False, decision_authority='report_only',
        policy_publication=False))
    atomic_write_json(folder / 'latest.json', index)
    return index

def _failure(root, day, exc):
    # Called while holding the date lock, so a stale failed worker cannot replace
    # another worker's successful terminal.
    error = dict(source_date=day, status='failed', error=str(exc)[:200],
                 adapter_sha256=consumer.H.file_sha(__file__))
    generation = consumer.S.digest(error)
    folder = _report_folder(root, day)
    output = folder / generation / 'result.json'
    failure = consumer.A.seal(dict(schema='samsung_tick_transition_forward_result_v1',
        **consumer.AUTHORITY, day=day, candidate_id=consumer.CANDIDATE, status='failed', error=error['error']))
    atomic_write_json(output, failure)
    result = consumer.A.seal(dict(schema='samsung_frozen_postclose_index_v1',
        owner='SamsungFrozenCandidateValidation1006', **error, generation=generation,
        result_path=str(output), result_file_sha256=consumer.H.file_sha(output),
        candidate_id=consumer.CANDIDATE, runtime_effect=False, actual_order_submitted=False,
        decision_authority='report_only', policy_publication=False, target_date=None))
    atomic_write_json(folder / 'latest.json', result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--date', required=True)
    parser.add_argument('--contract', type=Path)
    args = parser.parse_args()
    try:
        result = run(args.root, args.date, contract_path=args.contract)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps(dict(source_date=args.date, status='failed', error=str(exc)[:200])))
        raise SystemExit(1)
    print(json.dumps({k: result[k] for k in ('source_date', 'status', 'generation', 'result_path')}))


if __name__ == '__main__':
    main()
