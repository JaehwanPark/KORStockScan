"""Run isolated code fixtures and publish their exact-generation evidence only."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import uuid
from zoneinfo import ZoneInfo

from src.engine.monitoring import policy_generation_contract as generation
from src.engine.monitoring import policy_generation_validation as validation


def _assert_committed(family):
    paths = [*validation.plan_identity(family),
             *('src/engine/'+name for name in generation.COMPONENTS[family]),
             'src/engine/monitoring/policy_generation_contract.py',
             'src/engine/lifecycle/holding_window_generation.py']
    status = subprocess.check_output(['git','status','--porcelain','--',*paths],
                                     cwd=validation.ROOT,text=True)
    if status.strip():
        raise ValueError('fixture_publication_requires_committed_sources')


def validate(family, data, *, source_date, target_date, publish=False):
    data = Path(data).resolve()
    if publish:
        _assert_committed(family)
    code = generation.code_generation(family)
    plan = validation.plan_identity(family)
    for day in (source_date, target_date):
        if datetime.fromisoformat(day).date().isoformat() != day:
            raise ValueError('fixture_date_invalid')
    protected = [
        data/'report/entry_cancel_wait_tuning'/f'entry_cancel_wait_tuning_{source_date}.json',
        data/'report/rising_missed_classifier_prior'/f'rising_missed_classifier_prior_{source_date}.json',
        data/'report/monitor_snapshots'/f'holding_exit_observation_{source_date}.json',
        data/'report/reversal_auxiliary_tuning'/source_date/'evaluation.json',
        data/'runtime/runtime_release_selection.json',
        data/'runtime/policy_bootstrap'/f'runtime_policy_bootstrap_{target_date}.json',
        data/'runtime/policy_bootstrap'/f'runtime_policy_bootstrap_{target_date}.env',
    ]
    before = {str(path): validation.file_sha(path) if path.exists() else None for path in protected}
    destination = validation.fixture_path(data, family)
    if destination.exists() or destination.is_symlink():
        value, reference = validation.verify_fixture(data, family)
        return dict(status='verified_existing', family=family, fixture=reference,
                    passed_tests=value['passed_tests'], runtime_effect=False)
    run = data/'report/postclose_generation_validation/runs'/(
        datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%dT%H%M%S')+'-'+family+'-'+uuid.uuid4().hex[:8])
    run.mkdir(parents=True, exist_ok=False)
    # Deny real network access for the entire child interpreter. Mocked provider
    # tests remain available; any attempted connection fails the validation even
    # if application code catches its exception.
    guard = run/'fixture_network_guard.py'
    guard.write_text("""import json, socket
from pathlib import Path
attempts = []
def denied(*args, **kwargs):
    attempts.append('network_attempt_blocked')
    raise RuntimeError('fixture_network_forbidden')
def pytest_sessionstart(session):
    socket.socket.connect = denied
    socket.socket.connect_ex = denied
    socket.create_connection = denied
def pytest_sessionfinish(session, exitstatus):
    Path(__file__).with_name('network.json').write_text(json.dumps({'blocked_attempts': len(attempts)}))
    if attempts: session.exitstatus = 1
""")
    command = [sys.executable,'-B','-m','pytest','-q',*validation.PLANS[family],
               '--junitxml='+str(run/'tests.xml'),'-p','no:cacheprovider','-p','fixture_network_guard']
    start = datetime.now(ZoneInfo('Asia/Seoul')).isoformat()
    process = None
    def stop(signum, frame):
        raise InterruptedError('fixture_validation_interrupted')
    previous = signal.signal(signal.SIGTERM, stop)
    try:
        with (run/'tests.log').open('xb') as log:
            process = subprocess.Popen(command, cwd=validation.ROOT,
                env={**os.environ,'PYTHONPATH':str(run)+os.pathsep+str(validation.ROOT),'PYTHONDONTWRITEBYTECODE':'1'},
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            result = process.wait(timeout=180)
        if result != 0:
            raise ValueError('fixture_tests_failed:'+str(result))
        count = validation.junit_counts(run/'tests.xml', family)
        if json.loads((run/'network.json').read_text()) != {'blocked_attempts':0}:
            raise ValueError('fixture_network_attempted')
        after = {str(path): validation.file_sha(path) if path.exists() else None for path in protected}
        if before != after:
            raise ValueError('fixture_protected_artifact_changed')
        if code != generation.code_generation(family) or plan != validation.plan_identity(family):
            raise ValueError('fixture_code_changed_during_validation')
        body = dict(schema='postclose_generation_fixture_receipt_v1', family=family,code_sha256=code,
            status='pass',as_of=datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),validation_started_at=start,
            closure_tests=validation.PLANS[family],unresolved_findings=[],passed_tests=count,
            validation_plan=plan, validation_run=str(run),
            evidence={name:validation.file_sha(run/name) for name in ('tests.log','tests.xml','network.json')},
            protected_artifact_sha256=before, protected_unchanged=True,
            source_date=source_date, target_date=target_date,
            release_root=str(validation.ROOT), git_commit=subprocess.check_output(
                ['git','rev-parse','HEAD'],cwd=validation.ROOT,text=True).strip(),
            verification_scope='synthetic_source_comparison_selection_publication_native_reader; no_economic_acceptance',
            provider_calls=0, orders=0, **{key:False for key in validation.AUTHORITY_FALSE})
        body['receipt_sha256'] = generation.digest(body)
        candidate=run/'fixture.json';candidate.write_text(json.dumps(body,sort_keys=True,indent=2)+'\n')
        if publish:
            _assert_committed(family)
            # Atomic create; a competing or historical receipt is never replaced.
            os.link(candidate,destination)
            validation.verify_fixture(data,family)
        receipt=dict(status='pass',family=family,passed_tests=count,published=publish,
            fixture_path=str(destination) if publish else str(candidate),runtime_effect=False)
        (run/'result.json').write_text(json.dumps(receipt,indent=2)+'\n')
        return receipt
    except BaseException as exc:
        if process is not None and process.poll() is None:
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)
        (run/'failure.json').write_text(json.dumps(dict(status='failed',reason=type(exc).__name__+':'+str(exc)))+'\n')
        raise
    finally:
        signal.signal(signal.SIGTERM,previous)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family',choices=validation.PLANS,required=True)
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--source-date',required=True)
    parser.add_argument('--target-date',required=True)
    parser.add_argument('--publish',action='store_true')
    args=parser.parse_args(argv)
    print(json.dumps(validate(args.family,args.data_root,source_date=args.source_date,target_date=args.target_date,publish=args.publish),sort_keys=True))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
