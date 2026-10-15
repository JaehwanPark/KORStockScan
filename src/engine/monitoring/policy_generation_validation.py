"""Current code capability evidence for immutable historical native reports.

This additive reader never changes reports, policy selection, or runtime authority.
The old contract remains historical; the current fixture is independently verified.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
import stat
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

from src.engine.monitoring import policy_generation_contract as generation
from src.engine.scalping.main_stop_policy import bounded_object

ROOT = Path(__file__).resolve().parents[3]
PLANS = {
    'entry_cancel_wait': [
        'src/tests/test_entry_cancel_wait_tuning.py',
        'src/tests/test_entry_cancel_wait_runtime.py',
        'src/tests/test_entry_cancel_wait_attribution.py',
    ],
    'rising_missed': [
        'src/tests/test_rising_missed_classifier_prior.py',
        'src/tests/test_rising_missed_intraday_feedback.py',
    ],
    'holding_vote': [
        'src/tests/test_holding_path_vote_replay.py',
        'src/tests/test_holding_vote_numeric_successor.py',
        'src/tests/test_holding_exit_vote.py',
    ],
}
AUTHORITY_FALSE = ('runtime_effect', 'allowed_runtime_apply', 'actual_pid_consumed',
                   'actual_profit_verified', 'policy_published')


def file_bytes(path, limit=8*1024*1024):
    path = Path(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise ValueError('fixture_regular_bounded_file_required')
        raw = stream.read(limit+1)
        after = path.lstat()
    identity = lambda value: (value.st_dev,value.st_ino,value.st_size,value.st_mtime_ns,value.st_ctime_ns)
    if len(raw) > limit or len(raw) != before.st_size or identity(before) != identity(after):
        raise ValueError('fixture_read_changed_or_limit_exceeded')
    return raw


def file_sha(path, limit=8*1024*1024):
    return hashlib.sha256(file_bytes(path,limit)).hexdigest()


def plan_identity(family):
    paths = [*PLANS[family], 'src/engine/monitoring/policy_generation_validation.py',
             'src/engine/automation/policy_generation_fixture_validation.py']
    return {path: file_sha(ROOT/path) for path in paths}


def junit_counts(path, family, *, raw=None):
    root = ET.fromstring(file_bytes(path) if raw is None else raw)
    cases = list(root.iter('testcase'))
    if not cases or any(list(root.iter(tag)) for tag in ('failure', 'error', 'skipped')):
        raise ValueError('fixture_tests_not_all_passed')
    covered = {case.get('classname', '').rsplit('.', 1)[-1] for case in cases}
    if not {Path(name).stem for name in PLANS[family]} <= covered:
        raise ValueError('fixture_test_plan_incomplete')
    return len(cases)


def fixture_path(data, family):
    return Path(data)/'report/postclose_generation_validation'/f'{family}_{generation.code_generation(family)}.json'


def verify_fixture(data, family):
    path = fixture_path(data, family)
    value, sha = bounded_object(path, 65536)
    if (path.is_symlink() or value.get('schema') != 'postclose_generation_fixture_receipt_v1'
            or value.get('family') != family or value.get('status') != 'pass'
            or value.get('code_sha256') != generation.code_generation(family)
            or value.get('closure_tests') != PLANS[family]
            or value.get('unresolved_findings') != []
            or any(value.get(key) is not False for key in AUTHORITY_FALSE)
            or value.get('provider_calls') != 0 or type(value.get('provider_calls')) is not int
            or value.get('orders') != 0 or type(value.get('orders')) is not int
            or value.get('receipt_sha256') != generation.digest({k:v for k,v in value.items() if k!='receipt_sha256'})
            or value.get('validation_plan') != plan_identity(family)
            or value.get('protected_unchanged') is not True
            or not isinstance(value.get('protected_artifact_sha256'), dict)):
        raise ValueError('fixture_identity_or_authority_invalid')
    run = Path(value.get('validation_run', ''))
    expected_parent = (Path(data)/'report/postclose_generation_validation/runs').resolve()
    if run.is_symlink() or run.resolve().parent != expected_parent:
        raise ValueError('fixture_run_path_invalid')
    evidence = value.get('evidence')
    if not isinstance(evidence, dict) or set(evidence) != {'tests.log','tests.xml','network.json'}:
        raise ValueError('fixture_evidence_missing')
    raw = {name:file_bytes(run/name) for name in evidence}
    if any(hashlib.sha256(raw[name]).hexdigest() != digest for name,digest in evidence.items()):
        raise ValueError('fixture_evidence_changed')
    if json.loads(raw['network.json']) != {'blocked_attempts':0}:
        raise ValueError('fixture_network_attempted')
    count = junit_counts(run/'tests.xml', family, raw=raw['tests.xml'])
    if type(value.get('passed_tests')) is not int or value['passed_tests'] != count:
        raise ValueError('fixture_test_count_invalid')
    return value, dict(path=str(path), sha256=sha)


def current_fixture_observation(observed, data):
    """Supplement only a valid, same-code native contract lacking its fixture.

    No original bytes are rewritten. Real source/selection/sample gaps and the
    original contract status remain visible, independently of code capability.
    """
    family = observed.get('family')
    if (family not in PLANS or observed.get('status') != 'unverified'
            or observed.get('findings') != ['policy_generation_unverified']
            or observed.get('missing_components') != [] or observed.get('observation_complete') is not True
            or observed.get('native_validated') is not False):
        return observed
    path = fixture_path(data, family)
    if not path.exists() and not path.is_symlink():
        return observed
    try:
        fixture, reference = verify_fixture(data, family)
        relative = {
            'entry_cancel_wait': 'entry_cancel_wait_tuning/entry_cancel_wait_tuning_',
            'rising_missed': 'rising_missed_classifier_prior/rising_missed_classifier_prior_',
            'holding_vote': 'monitor_snapshots/holding_exit_observation_',
        }[family]
        expected = Path(data)/'report'/(relative+observed['source_date']+'.json')
        if Path(observed['artifact']) != expected:
            raise ValueError('fixture_native_report_path_invalid')
        payload, report_sha = bounded_object(Path(observed['artifact']), 8*1024*1024)
        native_payload = payload['holding_path_vote_replay'] if family=='holding_vote' else payload
        contract = native_payload['policy_generation']
        if observed.get('binding_repair') is not None:
            contract, binding = generation._read_holding_code_rebinding(
                Path(data), observed['source_date'], report_sha, payload)
            if binding != observed['binding_repair']:
                raise ValueError('fixture_report_binding_repair_changed')
        original = generation.inspect(contract, family=family, day=observed['source_date'],
                                      payload=native_payload, data_root=Path(data))
        if (original['status'] != 'unverified' or contract.get('fixture_receipt') is not None
                or report_sha != observed.get('report_sha256')
                or contract['contract_sha256'] != observed.get('contract_sha256')
                or contract['code_sha256'] != fixture['code_sha256']
                or any(original[key] != observed.get(key) for key in
                    ('source_generation','code_sha256','source_state','comparison_state','handoff_state'))):
            raise ValueError('fixture_preserved_report_generation_changed')
        # Native producer/reader, in memory, binds the verified current fixture
        # to the same source body. It grants code capability only.
        current = generation.native(native_payload, family=family, day=observed['source_date'], data_root=Path(data),
            source_state=contract['source_state'], comparison_state=contract['comparison_state'],
            handoff_state=contract['handoff_state'])
        verified = generation.inspect(current, family=family, day=observed['source_date'],
                                      payload=native_payload, data_root=Path(data))
        if (verified['status'] != 'verified' or current['fixture_receipt'] != reference
                or verified['source_generation'] != original['source_generation']):
            raise ValueError('fixture_native_reader_unverified')
        # Recheck the authoritative source after projection; never close a
        # concurrently replaced generation using the preceding bytes.
        if bounded_object(Path(observed['artifact']),8*1024*1024)[1] != report_sha:
            raise ValueError('fixture_report_changed_during_validation')
        result = deepcopy(observed)
        result.update(status='verified', findings=[], native_validated=False,
            current_code_capability_verified=True, historical_contract_status='unverified',
            verification_basis='current_fixture_for_preserved_native_report',
            current_fixture=reference, current_capability_contract_sha256=current['contract_sha256'])
        result['scopes'] = {family:{k:v for k,v in result.items()
            if k not in {'scopes','family','source_date','artifact'}}}
        return result
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as exc:
        return dict(observed, current_fixture_status='invalid', current_fixture_reason=str(exc))
