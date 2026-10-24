"""Native, report-only currentness beside an immutable PREOPEN holding source.

Monitoring owns this projection. It never rewrites the holding snapshot, policy,
bootstrap, or controller, and its receipt is not accepted by runtime consumers.
"""
from datetime import date, datetime
import fcntl
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.automation import main_trailing_research_handoff as native
from src.engine.automation.main_trailing_all_scope_research import _sealed, code_contract
from src.engine.lifecycle.holding_window_generation import byte_generation
from src.engine.scalping.pre_submit_delay_initial_policy import _atomic, digest

SCHEMA = 'main_trailing_monitor_currentness_v1'


def _same_scope_identity(old, current):
    if old == current:
        return True
    clocks = [value.get('as_of') for value in (old, current)]
    if any(type(value) not in (int, float) or not math.isfinite(value) or value <= 0 for value in clocks):
        return False
    return all(value.get('schema') == 'main_exit_scope_snapshot_v1' for value in (old, current)) and (
        {k:v for k,v in old.items() if k not in {'as_of', 'universe_snapshot_sha256'}} ==
        {k:v for k,v in current.items() if k not in {'as_of', 'universe_snapshot_sha256'}})


def _verify_scope_clock(report, path):
    """Verify the clock-dependent digest against the sealed native universe."""
    from src.engine.lifecycle import research_storage as storage
    from src.engine.scalping.main_exit_scope import build_scope, validate_scope
    manifest_path = Path(report['input_manifest_path'])
    if byte_generation(manifest_path) != report['input_manifest_generation']:
        raise ValueError('trailing_monitor_scope_manifest_changed')
    manifest = _sealed(manifest_path)
    scope = dict(report['scope'])
    if not 0 < scope['scope_count'] <= 80000:
        raise ValueError('trailing_monitor_scope_unbounded')
    scope['scopes'] = list(storage.iter_tree(path.parent, scope.pop('scopes_ref')))
    validate_scope(scope)
    expected = build_scope(manifest['universe'], as_of=manifest['as_of'],
        universe_source_sha256=manifest['universe_source_sha256'],
        operating=manifest.get('operating'), coverage=manifest.get('coverage'), custody=manifest.get('custody'))
    if scope != expected:
        raise ValueError('trailing_monitor_scope_manifest_mismatch')


def _paths(data, source, target):
    data = Path(data).resolve(strict=True)
    for day in (source, target):
        if date.fromisoformat(day).isoformat() != day:
            raise ValueError('trailing_monitor_date_invalid')
    if source >= target:
        raise ValueError('trailing_monitor_date_invalid')
    holding = data/'report/monitor_snapshots'/f'holding_exit_observation_{source}.json'
    receipt = data/'report/main_trailing_currentness'/source/target/(code_contract()+'.json')
    return data, holding, receipt


def _original(holding_path, holding, target):
    generation = byte_generation(holding_path)
    if holding_path.stat().st_size > 4*1024*1024:
        raise ValueError('trailing_monitor_holding_unbounded')
    if json.loads(holding_path.read_bytes()) != holding:
        raise ValueError('trailing_monitor_holding_changed')
    ext = holding['all_scope_trailing_research']
    path = Path(ext['report_path'])
    report = _sealed(path)
    report_generation = byte_generation(path)
    if (report.get('schema') != 'main_all_scope_exit_research_v2'
            or report.get('status') != 'complete'
            or report.get('source_date') != holding['date'] or report.get('target_date') != target
            or report.get('allowed_runtime_apply') is not False
            or ext.get('allowed_runtime_apply') is not False
            or ext.get('status') != 'complete' or ext.get('report_generation') != report_generation
            or ext.get('input_window_generation_sha256') != report['input_window_generation_sha256']
            or ext.get('initial_policy_sha256') != report['initial_policy']['policy_sha256']
            or ext.get('scope_count') != report['scope']['scope_count']
            or byte_generation(holding_path) != generation):
        raise ValueError('trailing_monitor_original_binding_invalid')
    return report, dict(holding_generation=generation, report_path=str(path), report_generation=report_generation)


def _extension(report, path, generation):
    return dict(report_path=str(path), report_generation=generation, status=report['status'],
                input_window_generation_sha256=report['input_window_generation_sha256'],
                initial_policy_sha256=report['initial_policy']['policy_sha256'],
                scope_count=report['scope']['scope_count'], allowed_runtime_apply=False)


def issue(data, *, source_date, target_date, report_path):
    """Publish only after full native source/partition/arithmetic verification."""
    data, holding_path, destination = _paths(data, source_date, target_date)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with (destination.parent/'.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if holding_path.stat().st_size > 4*1024*1024:
            raise ValueError('trailing_monitor_holding_unbounded')
        holding = json.loads(holding_path.read_bytes())
        old, original = _original(holding_path, holding, target_date)
        path = Path(report_path).resolve(strict=True)
        if not path.is_relative_to(data/'report/main_all_scope_trailing'/source_date/'generations'):
            raise ValueError('trailing_monitor_report_path_invalid')
        report, generation = native.verify_report(path, target_date=target_date)
        manifest = _sealed(Path(report['input_manifest_path']))
        if (report['source_date'] != source_date or Path(manifest['source_data_root']).resolve() != data
                or old['initial_policy'] != report['initial_policy']
                or not _same_scope_identity(old['scope'], report['scope'])):
            raise ValueError('trailing_monitor_parent_or_scope_changed')
        if old['scope'] != report['scope']:
            _verify_scope_clock(old, Path(original['report_path']))
            _verify_scope_clock(report, path)
        extension = _extension(report, path, generation)
        checked = native.observe_extension(dict(date=source_date, all_scope_trailing_research=extension),
                                           target_date=target_date, required=True)
        if checked['status'] != 'generation_current' or _original(holding_path, holding, target_date)[1] != original:
            raise ValueError('trailing_monitor_generation_changed')
        receipt = dict(schema=SCHEMA, source_date=source_date, target_date=target_date,
                       generated_at=datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),
                       original=original, extension=extension, code_contract_sha256=code_contract(),
                       full_native_validation=True, original_policy_preserved=True,
                       scope_identity_verified=True,
                       allowed_runtime_apply=False, runtime_effect=False, actual_pid_consumed=False)
        receipt['artifact_sha256'] = digest(receipt)
        if destination.exists():
            existing = _sealed(destination)
            if any(existing.get(k) != receipt[k] for k in receipt if k not in {'generated_at','artifact_sha256'}):
                raise ValueError('trailing_monitor_issued_generation_conflict')
            return existing
        _atomic(destination, receipt)
        return receipt


def observe(data, holding, *, target_date):
    """Bounded issued-generation observation; original source remains visible."""
    baseline = native.observe_extension(holding, target_date=target_date,
        required=(holding.get('meta') or {}).get('snapshot_profile') == 'postclose_exit')
    if baseline.get('findings') != ['main_trailing_research_handoff_invalid']:
        return baseline
    try:
        _, holding_path, receipt_path = _paths(data, holding['date'], target_date)
        if not receipt_path.exists():
            return baseline
        old, original = _original(holding_path, holding, target_date)
        receipt_generation = byte_generation(receipt_path)
        receipt = _sealed(receipt_path)
        if (receipt.get('schema') != SCHEMA or receipt.get('source_date') != holding['date']
                or receipt.get('target_date') != target_date or receipt.get('original') != original
                or receipt.get('code_contract_sha256') != code_contract()
                or receipt.get('full_native_validation') is not True
                or receipt.get('original_policy_preserved') is not True
                or receipt.get('scope_identity_verified') is not True
                or any(receipt.get(key) is not False for key in
                       ('allowed_runtime_apply','runtime_effect','actual_pid_consumed'))):
            raise ValueError('trailing_monitor_receipt_invalid')
        ext = receipt['extension']
        path = Path(ext['report_path'])
        if not path.is_relative_to(Path(data).resolve()/'report/main_all_scope_trailing'/holding['date']/'generations'):
            raise ValueError('trailing_monitor_report_path_invalid')
        report = _sealed(path)
        if old['initial_policy'] != report['initial_policy'] or not _same_scope_identity(old['scope'], report['scope']):
            raise ValueError('trailing_monitor_parent_or_scope_changed')
        result = native.observe_extension(dict(date=holding['date'], all_scope_trailing_research=ext),
                                          target_date=target_date, required=True)
        if result['status'] != 'generation_current':
            raise ValueError('trailing_monitor_revalidated_generation_invalid')
        if (_original(holding_path, holding, target_date)[1] != original
                or byte_generation(receipt_path) != receipt_generation):
            raise ValueError('trailing_monitor_generation_changed')
        return dict(result, basis='separate_full_native_revalidation',
                    original_findings=baseline['findings'], original=original,
                    currentness_receipt=str(receipt_path), policy_effect='unchanged', actual_pid_consumed=False)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        return dict(baseline, currentness_findings=[str(exc)])


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--source-date', required=True)
    parser.add_argument('--target-date', required=True)
    parser.add_argument('--verified-report', type=Path, required=True)
    args = parser.parse_args(argv)
    result = issue(args.data_root, source_date=args.source_date,
                   target_date=args.target_date, report_path=args.verified_report)
    print(json.dumps(dict(schema=result['schema'], source_date=result['source_date'],
                         target_date=result['target_date'], artifact_sha256=result['artifact_sha256'],
                         runtime_effect=False)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
