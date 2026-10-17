"""Preserve verified same-day policies across an authorized immutable code handoff.

Ownership: startup automation. This does not create PREOPEN success, policies,
orders, or trading authority; the native custody and bootstrap gates still apply.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from contextvars import ContextVar
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.automation import runtime_policy_bootstrap as bootstrap
from src.engine.infrastructure.runtime_release_router import selected_release
from src.utils.constants import DATA_DIR
from src.utils.market_day import is_krx_trading_day

KST = ZoneInfo("Asia/Seoul")
CONFIRM = "APPROVED_INTRADAY_POLICY_PRESERVING_RELEASE_HANDOFF"
_STOPPED_PREPARATION = ContextVar('intraday_stopped_preparation', default=None)
_NATIVE_PREDECESSOR = ContextVar('intraday_native_predecessor', default=None)
_OBSERVER_CUSTODY = ContextVar('intraday_observer_custody', default=None)
_PREDECESSOR_REVIEW = ContextVar('intraday_predecessor_review', default=None)

# Reviewed delivery/observation repair. Exact source pairs, not a blanket
# exception for the large runtime functions. Policy generation, quote timing
# and safety guards retain the original contract; any further byte change
# requires another review. Evidence: docs/audits/machine-auxiliary-signal-delivery-review-2026-10-12.md.
REVIEWED_ENTRY_CONSUMER_SOURCES = {
    # Exact native readiness/claim/timing repair reviewed for this code-only handoff.
    # Evidence: docs/audits/main-native-readiness-deployment-review-2026-10-12.md.
    'src/engine/monitoring/submission_bottleneck_monitor.py': (
        '26300fee49e3ca28568b07db2b0b7030e577c8070a78bef2477340f34dfba981',
        'd08f8e220cf76f2b2b867e40eb5382bf17491391161277367acf407143e65a21'),
    'src/engine/kiwoom_sniper_v2.py': (
        '4cbd06363b1156761fd748c51ac9fbb4f54e69b64771f9f86e6770bba5ce177c',
        '45a139a2ed413afb888cd244ae73d60d5f312b503a8e1c54cc1ce599b048d279'),
    'src/engine/sniper_state_handlers.py': (
        '4caaddc9d38008bd55968e2ec7b0553bd50e294c1f687eabf588f34a972c847d',
        '773ba18e4297ffb85be10f53d9490a4f1860f68dab0472b1ead2f1d4ee5c5117'),
    'src/engine/scalping/scanner_async_eval.py': (
        '89742c044a782e9058ab43f91cc3969f0910beff506b51218079225fb6a28220',
        'bfb445c6d44d717ae1fa0cbac6bef5774daadff06199128dcec22c12f7998239'),
    'src/utils/pipeline_event_logger.py': (
        '35bc6825a1e6788a8cb876a6c7eb2774581bc7bc6771f90cb42d2cfe70fcfd1a',
        '58dd5b4ba0ce91a248cebf8a608974caba13080226e139e779f512500b4b4c5f'),
    'src/engine/ai_engine_openai.py': (
        '3f3d0baed55847c146c5ef86ca3d1ca52742f307ffc5004e05b038b89a1e8796',
        'b1c79f0fdce031b947280b3472101c5b87797dedc1b7a183eb64a973bbbeb5ae'),
}

# Source-exact shared-deadline latency repair; retain the older reviewed pairs
# above for their already-consumed handoffs. This is no function-wide exemption.
# Evidence: docs/audits/main-entry-auxiliary-shared-deadline-latency-implementation-review-2026-10-13.md.
REVIEWED_ENTRY_LATENCY_SOURCES = {
    'src/engine/sniper_state_handlers.py': (
        '5c0b5e1b97e50ed1bd80c4084795a40eaa430c62a8d52cb30b338dbbf7c574ca',
        '903cd8b37e9e60ecfe51a454a1933484f08d0c3c1c7629f7e55e369608770425'),
    'src/engine/kiwoom_sniper_v2.py': (
        '96319c0071dfce04980af151ff9e22b91352a704281bb727c8e68d604ee6aa20',
        'd19c471856511889cf9728a3fee7f13c4bcdfce29566dbea80ae5b581d9e8777'),
    'src/engine/scalping/scanner_async_eval.py': (
        'bfb445c6d44d717ae1fa0cbac6bef5774daadff06199128dcec22c12f7998239',
        '54d8584efa5350575d687b92486e205702f94cfde7a87da0acda46d1f3522748'),
    'src/engine/ai_engine_openai.py': (
        '4d5ff0cc0451365f17feb8ed8f6a113f984abf416f24ac7bd5cb24f2ca596eed',
        '34332f4541b381184ca47d371ecc6598b6f2e10534085bf3893c76fef553c7f2'),
}

# Final synchronous provider-boundary repair; previous consumed pairs remain
# valid for their immutable releases. Exact source pair, no broader exemption.
REVIEWED_ENTRY_BOUNDARY_SOURCES = {
    'src/engine/ai_engine_openai.py': (
        '4d5ff0cc0451365f17feb8ed8f6a113f984abf416f24ac7bd5cb24f2ca596eed',
        '7a2d9795aa7501e0f510368f59282d849456c310c91b46d993d2d540867d678a'),
}

# Response transport health and fresh post-response validation. Exact reviewed
# bytes only; preserve every previously consumed source pair.
# Evidence: docs/audits/main-restart-machine-monitoring-and-timeout-structural-repair-review-2026-10-13.md.
REVIEWED_ENTRY_RESPONSE_SOURCES = {
    'src/engine/ai_engine_openai.py': (
        '4d5ff0cc0451365f17feb8ed8f6a113f984abf416f24ac7bd5cb24f2ca596eed',
        'dabda2cb9fee6fd17263465f38866d90ec66f62b7305a2b5bb7a8dd9fc9a1671'),
}

# Diagnostic state snapshots reference successfully appended canonical replay
# evidence instead of echoing its frozen code. Older release pairs stay valid.
REVIEWED_ENTRY_STORAGE_SOURCES = {
    'src/engine/sniper_state_handlers.py': (
        '5c0b5e1b97e50ed1bd80c4084795a40eaa430c62a8d52cb30b338dbbf7c574ca',
        '0afbd461d2ba0f60fa385179c0f03a7c0aaf0e3972e9b73401776012519783fb'),
}

# Reviewed joint/source diagnostics and compact replay context. The original
# policy and every order guard remain bound; only these exact bytes qualify.
# Evidence: docs/audits/main-joint-operating-and-source-repair-implementation-review-2026-10-13.md.
REVIEWED_JOINT_CONSUMER_SOURCES = {
    'src/engine/sniper_state_handlers.py': (
        '5c0b5e1b97e50ed1bd80c4084795a40eaa430c62a8d52cb30b338dbbf7c574ca',
        'fd35f4ccd99ab3aa665737253c5209ec84755a6b67152b3ff0552ae5c4a8d52d'),
    'src/engine/kiwoom_sniper_v2.py': (
        '96319c0071dfce04980af151ff9e22b91352a704281bb727c8e68d604ee6aa20',
        '51280b79c7eee85279c9d649c76888cb03954f73c18c1e0ba41a863c4ea8a0a1'),
    'src/engine/monitoring/submission_bottleneck_monitor.py': (
        'd08f8e220cf76f2b2b867e40eb5382bf17491391161277367acf407143e65a21',
        '95bd122be3b47d18236c2cc1127eefc9d0b9dd60771cf387637e9c838790e6fd'),
}

# Reviewed optional REST removal and completed-only initial entry inputs.
# Exact original PREOPEN-to-candidate bytes; retain all earlier consumed pairs.
# Evidence: docs/audits/main-rest-call-removal-and-reduced-input-implementation-review-2026-10-13.md.
REVIEWED_REST_REDUCTION_SOURCES = {
    'src/engine/sniper_state_handlers.py': (
        '5c0b5e1b97e50ed1bd80c4084795a40eaa430c62a8d52cb30b338dbbf7c574ca',
        'b7435b6001fc5901f601879a08fa4e61b7c337187e1ac58db5e93984768beaa3'),
    'src/engine/kiwoom_sniper_v2.py': (
        '96319c0071dfce04980af151ff9e22b91352a704281bb727c8e68d604ee6aa20',
        '6f1abc2ad7c532d693b832fb041ff519874ce141b52d2f1c724b445467440c0e'),
}

# Observer-only verification reuse; original publication/startup checks remain full.
REVIEWED_IO_OBSERVER_SOURCES = {
    'src/engine/automation/runtime_policy_bootstrap.py': (
        'f58cafa2207bbb2f1457173ff2d63bb41ca038ddb948c25df4f18b12c9e1499b',
        '0df0b5d81707fe66bd38f140a3bcb3c40d7d526d9afa55755a87b8dc8123d5a8'),
}

# Exact original PREOPEN to reviewed digest/observer bytes. No policy verdict reuse.
# Evidence: docs/audits/main-io-residual-implementation-review-2026-10-14.md.
REVIEWED_IO_DIGEST_SOURCES = {'src/engine/automation/runtime_policy_bootstrap.py': ('0df0b5d81707fe66bd38f140a3bcb3c40d7d526d9afa55755a87b8dc8123d5a8',
                                                       '7a2e67d6d537ccc0a322bbbde8935f96de74869bc48e456bd13071225dd84b56'),
 'src/engine/monitoring/submission_bottleneck_monitor.py': ('95bd122be3b47d18236c2cc1127eefc9d0b9dd60771cf387637e9c838790e6fd',
                                                            'fa572589c6b2f0ceedd943f16195ac43573d02d285438fd6c28d23e4a1157be9'),
 'src/engine/lifecycle/holding_window_generation.py': ('5f80256f9484c5fb485502bbdad461639c4d471d070fabde37c1743c3c8fd444',
                                                    '2d9a6c71c088671ff4349117d4df302dec46ebb55f39e98beca703c9fac28d0a')}

# Incumbent stop consumer compatibility only; numerical selection and research
# remain pinned to the full current implementation generation.
# Evidence: docs/audits/main-entry-auxiliary-shared-deadline-latency-implementation-review-2026-10-13.md.
REVIEWED_STOP_CONSUMER_SOURCES = {
    'src/engine/scalping/main_stop_policy.py': (
        '70fde9e700d3a56d873029ddde2824d4f166d31301199833da87dc3c02e6216f',
        'c444f74e9da0339b564543322da389bcbe38552c4ed56531e8ebf5c21676752e'),
    'src/engine/automation/main_stop_postclose.py': (
        'efb6eefeeca91b6a91891dffee06cfff996f47095ef70aa637d9afb0f0613a7d',
        '68628fd7c9758946344c5841b90d8073929665d2b61eba40041c74fabc843255'),
}


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read(path):
    value = json.loads(Path(path).read_text())
    if not isinstance(value, dict):
        raise ValueError("intraday_handoff_object_required")
    return value


def _native_predecessor(day, commit, previous, previous_commit, identity, path, sha):
    """Verify immutable evidence captured while the native Main was alive.

    This never infers old consumption from a stopped process or writes a fake
    intraday consumed receipt. The ordered transition owns the original proof.
    """
    expected = DATA_DIR / 'runtime/release_transitions' / day / commit / 'native-predecessor.json'
    if str(path) != str(expected) or expected.is_symlink() or _sha(expected) != sha:
        raise ValueError('intraday_native_predecessor_hash_invalid')
    value = _read(expected)
    proof = value.get('verification') or {}
    before = expected.parent / 'selection-before.json'
    selection = _read(before)
    manifest = _read(bootstrap.manifest_path(day))
    index = DATA_DIR / 'runtime/policy_bootstrap/prepared' / day / 'latest.json'
    ref = _read(index)
    receipt = Path(ref['receipt_path'])
    required = {str(p) for p in [bootstrap.env_path(day), bootstrap.manifest_path(day),
                                _preopen_path(day), index, receipt]}
    if (value.get('schema') != 'native_preopen_predecessor_v1'
            or value.get('authority') != 'APPROVED_ORDERED_INTRADAY_DEPLOY_AND_RESTART'
            or value.get('candidate_commit') != commit
            or proof.get('schema') != 'intraday_pid_consumption_verification_v1'
            or proof.get('status') != 'pass' or proof.get('basis') != 'native_preopen'
            or proof.get('actual_pid_consumed') is not True or proof.get('target_date') != day
            or proof.get('pid_identity') != identity or not identity.get('start_ticks')
            or identity.get('cwd') != str(Path(previous) / 'src')
            or proof.get('selected_release_commit') != previous_commit
            or proof.get('release_root') != str(previous)
            or proof.get('manifest_sha256') != manifest.get('manifest_sha256')
            or manifest.get('target_date') != day
            or manifest.get('selected_release_sha') != previous_commit
            or _preopen(day).get('selected_release_commit') != previous_commit
            or selection.get('actual_pid_consumed') is not True
            or selection.get('schema') != 'runtime_release_selection_v1'
            or selection.get('git_commit') != previous_commit
            or selection.get('release_root') != str(previous)
            or (selection.get('actual_pid_receipt') or {}).get('pid') != identity.get('pid')
            or value.get('selection_before_sha256') != _sha(before)
            or receipt.resolve().parent.parent != index.parent.resolve()
            or value.get('prepared_receipt_path') != str(receipt)
            or value.get('prepared_receipt_sha256') != ref.get('receipt_sha256')
            or _sha(receipt) != ref.get('receipt_sha256')
            or set(value.get('frozen_files', {})) != required
            or any(_sha(p) != s for p, s in value['frozen_files'].items())):
        raise ValueError('intraday_native_predecessor_binding_invalid')
    return dict(path=str(expected), sha256=sha, identity=identity, verification=proof,
                frozen_files=value['frozen_files'])


def preserve_checklist(day):
    """Save the exact already-sealed document before authorized owner edits."""
    index=DATA_DIR/'runtime/policy_bootstrap/prepared'/day/'latest.json'
    ref=_read(index);prepared_path=Path(ref['receipt_path'])
    if _sha(prepared_path)!=ref['receipt_sha256']:
        raise ValueError('intraday_original_prepared_invalid')
    prepared=_read(prepared_path)
    if prepared.get('status')!='prepared_verified' or prepared.get('target_date')!=day:
        raise ValueError('intraday_original_prepared_invalid')
    controller=_read(DATA_DIR/'report/postclose_done_controller'/('postclose_done_controller_'+prepared['source_date']+'.json'))
    strict=_read(controller['verification_attempt_path'])
    expected=strict['generation_binding']['checklist_sha256']
    source=DATA_DIR.parent/'docs/checklists'/(day+'-stage2-todo-checklist.md')
    content=source.read_bytes()
    if hashlib.sha256(content).hexdigest()!=expected:
        raise ValueError('intraday_checklist_not_current_sealed_generation')
    dest=DATA_DIR/'runtime/policy_bootstrap/historical_checklists'/(expected+'.md')
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():
        if dest.read_bytes()!=content:raise ValueError('intraday_historical_checklist_snapshot_changed')
    else:
        with dest.open('xb') as out:out.write(content);out.flush();os.fsync(out.fileno())
    return dict(path=str(dest),sha256=expected,source_date=prepared['source_date'],target_date=day)


def _historical_predecessor(day, commit, expected):
    """Reuse only a snapshot sealed and actually consumed by the predecessor."""
    path, consumed_path = _paths(day, commit)
    prior, consumed = _read(path), _read(consumed_path)
    historical = (prior.get('postclose_source_reseal') or {}).get('historical_checklist') or {}
    snapshot = path.parent / (commit + '.historical-checklist.md')
    if (prior.get('schema') != 'intraday_policy_preserving_release_handoff_v1'
            or prior.get('status') != 'prepared_verified' or prior.get('authority') != CONFIRM
            or prior.get('target_date') != day or prior.get('selected_release_commit') != commit
            or consumed.get('schema') != 'intraday_policy_preserving_consumption_v1'
            or consumed.get('status') != 'pass' or consumed.get('actual_pid_consumed') is not True
            or consumed.get('target_date') != day or consumed.get('selected_release_commit') != commit
            or consumed.get('handoff_sha256') != _sha(path)
            or historical.get('path') != str(snapshot) or historical.get('sha256') != expected
            or historical.get('git_path') != 'docs/checklists/' + day + '-stage2-todo-checklist.md'
            or prior.get('frozen_files', {}).get(str(snapshot)) != expected or _sha(snapshot) != expected):
        raise ValueError('intraday_historical_predecessor_invalid')
    return historical, {'handoff_path': str(path), 'handoff_sha256': _sha(path),
                        'consumed_path': str(consumed_path), 'consumed_sha256': _sha(consumed_path)}


def _paths(day, commit):
    root = DATA_DIR / "runtime/policy_bootstrap/intraday_handoff" / day
    return root / f"{commit}.json", root / f"{commit}.consumed.json"


def _identity(pid):
    proc = Path("/proc") / str(int(pid))
    fields = (proc / "stat").read_text().rsplit(")", 1)[1].split()
    if fields[0] == "Z":
        raise ValueError("intraday_pid_zombie")
    cmdline = (proc / "cmdline").read_bytes().split(b"\0")
    if not any(arg.endswith(b"bot_main.py") for arg in cmdline):
        raise ValueError("intraday_pid_not_main")
    return {"pid": int(pid), "start_ticks": fields[19], "cwd": str((proc / "cwd").resolve(strict=True))}


def _selection(*, require_selected_cwd=True):
    root, commit = selected_release(DATA_DIR.parent)
    if require_selected_cwd and Path.cwd().resolve() not in (root, root / "src"):
        raise ValueError("intraday_handoff_selected_root_required")
    return root, commit


def _today(day, now):
    current = (now or datetime.now(KST)).astimezone(KST)
    if day != current.date().isoformat() or not is_krx_trading_day(current.date()):
        raise ValueError("intraday_handoff_not_current_trading_day")
    return current


def _preopen_path(day):
    return DATA_DIR / "report/threshold_cycle_preopen_status" / f"threshold_cycle_preopen_{day}.status.json"


def _preopen(day):
    value = _read(_preopen_path(day))
    updated = datetime.fromisoformat(str(value.get("updated_at") or ""))
    if (value.get("target_date") != day or value.get("status") != "succeeded"
            or value.get("exit_code") != 0 or value.get("runtime_env_exists") is not True
            or updated.tzinfo is None or updated.astimezone(KST).date().isoformat() != day):
        raise ValueError("intraday_original_preopen_invalid")
    return value


def verify_entry_consumer_code(day, *, family, policy_sha, expected, paths, actual):
    """Verify frozen policy custody and a narrow, immutable entry-only code delta.

    This also works before prepare seals its own handoff: the predecessor must
    have consumed the original manifest and still be the exact live process.
    No policy bytes, producer selection or research acceptance are rewritten.
    """
    if (DATA_DIR/'runtime/policy_bootstrap/code_handoffs'/day).exists():
        from src.engine.automation.prepared_policy_code_handoff import verify as verify_prepared_code
        prepared = verify_prepared_code(DATA_DIR, day, family=family, policy_sha=policy_sha,
                                        expected=expected, paths=paths, actual=actual)
        if prepared is not None:
            return prepared
    _today(day, None)
    root, commit = _selection(require_selected_cwd=False)
    code_root, code_commit = root, commit
    if Path(__file__).resolve().parents[3] != root:
        review = _PREDECESSOR_REVIEW.get()
        if (not review or review['day'] != day or review['root'] != root
                or review['commit'] != commit or review['code_root'] != Path(__file__).resolve().parents[3]
                or _identity(review['identity']['pid']) != review['identity']):
            raise ValueError('entry_consumer_release_mismatch')
        code_root, code_commit = review['code_root'], review['code_commit']
    manifest = _read(bootstrap.manifest_path(day))
    original = _preopen(day)
    origin = manifest.get('selected_release_sha')
    if not origin or origin != original.get('selected_release_commit'):
        raise ValueError('entry_consumer_origin_invalid')
    if family == 'pre_submit_delay':
        bound = manifest.get('pre_submit_delay_handoff') or {}
        if (bound.get('policy_sha256') != policy_sha
                or bound.get('code_contract_sha256') != expected or bound.get('target_date') != day):
            raise ValueError('entry_consumer_policy_binding_invalid')
    elif family == 'holding_vote':
        bound = manifest.get('holding_path_vote_policy_receipt') or {}
        if bound.get('bundle_sha256') != policy_sha or bound.get('target_date') != day:
            raise ValueError('entry_consumer_policy_binding_invalid')
    elif family == 'main_stop':
        bound = manifest.get('main_stop_confirmation_receipt') or {}
        if (bound.get('policy_sha256') != policy_sha or bound.get('target_date') != day
                or bound.get('status') != 'verified_carried'):
            raise ValueError('entry_consumer_policy_binding_invalid')
    else:
        raise ValueError('entry_consumer_family_invalid')
    current_path, consumed_path = _paths(day, commit)
    if current_path.exists():
        # A policy already consumed by this exact live PID keeps its sealed
        # authority when the editable work checklist changes. No new launch or
        # policy activation uses this read-only proof.
        checked = (_verify_consumed_handoff(day, commit) if consumed_path.exists()
                   else verify(day, commit))
        if checked.get('status') != 'pass':
            raise ValueError('entry_consumer_handoff_invalid')
    else:
        native = _NATIVE_PREDECESSOR.get()
        if native is not None:
            proof = native['verification']
            identity = native['identity']
            if (_STOPPED_PREPARATION.get() != (day, identity['pid'], proof['release_root'])
                    or proof['selected_release_commit'] != origin
                    or Path('/proc', str(identity['pid'])).exists()):
                raise ValueError('entry_consumer_native_predecessor_not_stopped')
            _native_predecessor(day, commit, proof['release_root'], origin, identity,
                                native['path'], native['sha256'])
            changed = _verify_entry_code_delta(root, commit, origin, paths, expected)
            return dict(status='verified_intraday_consumer_repair', target_date=day,
                policy_sha256=policy_sha, origin_commit=origin, release_commit=commit,
                code_contract_sha256=expected, runtime_code_contract_sha256=actual,
                changed_consumer_paths=changed, policy_effect='unchanged')
        selection = _read(DATA_DIR / 'runtime/runtime_release_selection.json')
        previous = selection.get('previous_git_commit')
        prior_path, consumed_path = _paths(day, previous)
        prior, consumed = _read(prior_path), _read(consumed_path)
        if (selection.get('approved_by') != 'user'
                or selection.get('approval_scope') not in {
                    'machine_auxiliary_path_repair_deploy_and_restart',
                    'entry_input_deadline_repair_deploy_and_restart',
                    'ordered_intraday_deploy_and_restart'}
                or prior.get('schema') != 'intraday_policy_preserving_release_handoff_v1'
                or prior.get('authority') != CONFIRM or prior.get('status') != 'prepared_verified'
                or prior.get('target_date') != day or prior.get('selected_release_commit') != previous
                or prior.get('release_root') != selection.get('previous_release_root')
                or consumed.get('schema') != 'intraday_policy_preserving_consumption_v1'
                or consumed.get('status') != 'pass' or consumed.get('actual_pid_consumed') is not True
                or consumed.get('target_date') != day or consumed.get('selected_release_commit') != previous
                or consumed.get('handoff_sha256') != _sha(prior_path)
                or consumed.get('release_root') != prior.get('release_root')
                or consumed.get('manifest_sha256') != manifest.get('manifest_sha256')):
            raise ValueError('entry_consumer_predecessor_invalid')
        identity = consumed.get('pid_identity') or {}
        stopped = _STOPPED_PREPARATION.get() == (day, identity.get('pid'), prior['release_root'])
        if (not identity.get('start_ticks')
                or identity.get('cwd') != str(Path(prior['release_root']) / 'src')
                or (Path('/proc', str(identity.get('pid'))).exists() if stopped
                    else _identity(identity.get('pid')) != identity)):
            raise ValueError('entry_consumer_predecessor_pid_changed')
        required = (bootstrap.manifest_path(day), bootstrap.env_path(day), _preopen_path(day))
        if any(prior.get('frozen_files', {}).get(str(p)) != _sha(p) for p in required):
            raise ValueError('entry_consumer_original_generation_changed')
    changed = _verify_entry_code_delta(code_root, code_commit, origin, paths, expected)
    return dict(status='verified_intraday_consumer_repair', target_date=day,
        policy_sha256=policy_sha, origin_commit=origin, release_commit=commit,
        code_contract_sha256=expected, runtime_code_contract_sha256=actual,
        changed_consumer_paths=changed, policy_effect='unchanged')


# Reviewed B0/B2/B3/B4 consumer repair; original PREOPEN policy and guards stay bound.
REVIEWED_NONFIXED_SUBMIT_SOURCES = {'src/engine/monitoring/submission_bottleneck_monitor.py': ('95bd122be3b47d18236c2cc1127eefc9d0b9dd60771cf387637e9c838790e6fd',
                                                            'ab743fd49b99cef9c9c3570fc8b542e3b7f54f983335da5bbdfc5465f5e9943a'),
 'src/engine/ai_engine_openai.py': ('dabda2cb9fee6fd17263465f38866d90ec66f62b7305a2b5bb7a8dd9fc9a1671',
                                    '6aa60869d8516af5222902761f412d87864125c8f160a2b6866aecae57d7dc58'),
 'src/engine/sniper_state_handlers.py': ('b7435b6001fc5901f601879a08fa4e61b7c337187e1ac58db5e93984768beaa3',
                                         'ff7e21f742986c71711b79dc45c2044291f6e6b80155e343b7ccd1424721e2c4'),
 'src/engine/kiwoom_sniper_v2.py': ('6f1abc2ad7c532d693b832fb041ff519874ce141b52d2f1c724b445467440c0e',
                                    '2498fb498de2d796fd9abc695caad99ccc61b914c2999a640d88f3f5c96f8dac'),
 'src/engine/scalping/scanner_async_eval.py': ('54d8584efa5350575d687b92486e205702f94cfde7a87da0acda46d1f3522748',
                                               'f0dc2bbeca1d3365185df9dac27765e7ec8f16d488a1ef352646374517679441')}

# Exact PREOPEN-to-reviewed projection and native-ready delivery consumer bytes.
# Evidence: docs/audits/entry-split-projection-and-main-delivery-implementation-review-2026-10-14.md.
REVIEWED_ENTRY_PROJECTION_DELIVERY_SOURCES = {'src/engine/ai_engine_openai.py': ('dabda2cb9fee6fd17263465f38866d90ec66f62b7305a2b5bb7a8dd9fc9a1671',
                                    '3831d30ef13ab190b07b64d8159d2e2c23ee6ce4b124f0c6504cb053ca145a3a'),
 'src/engine/kiwoom_sniper_v2.py': ('6f1abc2ad7c532d693b832fb041ff519874ce141b52d2f1c724b445467440c0e',
                                    'bb8cc6f224428a073f60826f8aa70e97d4b68b0383c907d681b8be5473a2d7c6'),
 'src/engine/monitoring/submission_bottleneck_monitor.py': ('95bd122be3b47d18236c2cc1127eefc9d0b9dd60771cf387637e9c838790e6fd',
                                                            'c1abc77a5bfdc983bb4cdf5fa02cd886337f9b71b68204906f6fbe476cdac723'),
 'src/engine/runtime_approval_summary.py': ('ed940e9fd88d328b489400055aceba793b9d0ad83b591053fb1912ac501e1aa3',
                                            'cc43d8de315cc07cd9545c06d1ce4fbfa32eb432d52d39ccb67b16e22f0c8cfd')}


# Canonical trusted data mount in the report-only entry-split consumer.
REVIEWED_ENTRY_PROJECTION_MOUNT_SOURCES = {'src/engine/monitoring/submission_bottleneck_monitor.py': ('95bd122be3b47d18236c2cc1127eefc9d0b9dd60771cf387637e9c838790e6fd',
                                                            'd276463a93a03a3c161a202811056eeae88a5def1e684ea3d0f5ee8a6217b7eb')}


# Report-only observer generation and first-current-publication ordering.
REVIEWED_STARTUP_OBSERVER_SOURCES = {'src/engine/monitoring/submission_bottleneck_monitor.py': ('95bd122be3b47d18236c2cc1127eefc9d0b9dd60771cf387637e9c838790e6fd', '112e22fde60ceb305450183883ffe6e3b338df6eb47e8c5d3ce78c282b968558')}

# Source-exact observer availability and bounded handoff diagnosis; no trading authority.
# Evidence: docs/audits/entry-split-projection-and-main-delivery-implementation-review-2026-10-14.md section8.
REVIEWED_OBSERVER_HEALTH_SOURCES = {'src/engine/monitoring/submission_bottleneck_monitor.py': ('95bd122be3b47d18236c2cc1127eefc9d0b9dd60771cf387637e9c838790e6fd', '6287ec98260f02ae85e61a2f25147d3011a89ebb276a962f215888fcd409f541')}


# Exact original PREOPEN-to-reviewed submission and observer repair.
# Preserve native deadlines, policy values, custody and every order guard.
# Evidence: docs/audits/main-submission-crisis-timeout-implementation-review-2026-10-14.md.
REVIEWED_SUBMISSION_TIMEOUT_SOURCES = {
    'src/engine/ai_engine_openai.py': (
        'dabda2cb9fee6fd17263465f38866d90ec66f62b7305a2b5bb7a8dd9fc9a1671',
        '58aa3ca78af08ef2cac6ec0501cc212947c4c5fa743c58b2daea26c0ba205937',
    ),
    'src/engine/sniper_state_handlers.py': (
        'b7435b6001fc5901f601879a08fa4e61b7c337187e1ac58db5e93984768beaa3',
        'b87f2ecdd7ef43a9f5268e06a5a9fbf8991223acffd58c3258aec68d77832500',
    ),
    'src/engine/scalping/scanner_async_eval.py': (
        '54d8584efa5350575d687b92486e205702f94cfde7a87da0acda46d1f3522748',
        'bfd354bbfbc371e912e873a3cbb40fd1ec2b9f5a78427602f214cfb0543b1d21',
    ),
    'src/engine/monitoring/submission_bottleneck_monitor.py': (
        '95bd122be3b47d18236c2cc1127eefc9d0b9dd60771cf387637e9c838790e6fd',
        '3f53a161bf5ca4857ec0b6b817ffe1c5bbf0b5e8712444334a421e200f9a40a4',
    ),
}


# Exact original PREOPEN-to-reviewed report-only terminal-session census.
# Earlier consumed source pairs remain valid; no machine/entry policy changes.
# Evidence: docs/audits/main-submission-crisis-timeout-implementation-review-2026-10-14.md.
REVIEWED_OBSERVER_TERMINAL_SESSION_SOURCES = {
    'src/engine/monitoring/submission_bottleneck_monitor.py': (
        '95bd122be3b47d18236c2cc1127eefc9d0b9dd60771cf387637e9c838790e6fd',
        '90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d',
    ),
}


# Exact native 2026-10-15 PREOPEN-to-reviewed venue/pending observer repair.
# No source or signal guard is waived; retain all earlier consumed pairs.
# Evidence: docs/audits/main-premarket-error-repair-and-restart-2026-10-15.md.
REVIEWED_PREMARKET_OBSERVER_SOURCES = {
    'src/engine/monitoring/submission_bottleneck_monitor.py': (
        '90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d',
        '7484dde211aeca61eb8172072f432c7d24bf7803e39c0f73ef9561cb64d0bfcf',
    ),
}


# Exact PREOPEN origin to active-report and native fixed-watch wait repair.
# Earlier deployed pairs remain verifiable; no policy or execution change.
# Evidence: docs/audits/main-premarket-error-repair-and-restart-2026-10-15.md.
REVIEWED_ACTIVE_OBSERVER_SOURCES = {
    'src/engine/monitoring/submission_bottleneck_monitor.py': (
        '90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d',
        'dd164faf5619deb20eef0456cd1187164f09d7f2094c474a2c691e9b700a253f',
    ),
}


# Exact PREOPEN to quiet current-PID/index and pre-birth incident classification.
# Capability receipts are separate report-only evidence; policies stay unchanged.
# Evidence: docs/audits/main-premarket-error-repair-and-restart-2026-10-15.md.
REVIEWED_CURRENT_OBSERVER_SOURCES = {
    'src/engine/monitoring/submission_bottleneck_monitor.py': (
        '90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d',
        '8525a03215257c97d8497ad6a55f4b9c7ffd543763c35d31e3730c85759f2221',
    ),
}


# Exact source-bound regular-session observer and approved 92785b7da integration.
# Historical policies/receipts stay intact; entry scheduling retains original TTL.
# Evidence: docs/audits/main-premarket-error-repair-and-restart-2026-10-15.md.
REVIEWED_NATIVE_HANDOFF_INTEGRATION_SOURCES = {
    'src/engine/monitoring/submission_bottleneck_monitor.py': (
        '90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d',
        '628d60031f1b787ad8fe661a261063f6925276e189fd6116d1948dd7db479f8a',
    ),
    'src/engine/sniper_state_handlers.py': (
        'b87f2ecdd7ef43a9f5268e06a5a9fbf8991223acffd58c3258aec68d77832500',
        'b39ddafe82bfbeab1d48502cce349b0e355e6008a1012a661d3e71973e2afe0e',
    ),
    'src/engine/monitoring/runtime_performance.py': (
        '3021477fe2ce6841e2d8acb734fc2fe0812939cd5b1be74333d18c2e6ed379f9',
        '767fe6bb4e874d8d2e6b56a693f028ecebc02f30ea8cf96a050e47ca6b76ebf8',
    ),
}


# Observer continuation separates small incident/cursor custody from full reports.
# Exact origin/successor pair; no policy or trading path changed.
REVIEWED_OBSERVER_STATE_READER_SOURCES = {
    'src/engine/monitoring/submission_bottleneck_monitor.py': (
        '90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d',
        'f4815942b04cf7cfda9d6db977d9987eb3a5d549e69a0ecdf5a77de10931ef22',
    ),
}


# Native incomplete observations retain UNKNOWN/expired evidence without admission.
# Exact reviewed source pair; see the 10:01 repair in the 2026-10-15 audit.
REVIEWED_NATIVE_INCOMPLETE_OBSERVER_SOURCES = {
    'src/engine/monitoring/submission_bottleneck_monitor.py': (
        '90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d',
        'ad8d684a71c2e6e8917f4a9db539da3df8ed1ef5b77b48cc6c892defc4318582',
    ),
}


# Exact report-only native feature-gap census; no admission or source-coverage grant.
# Evidence: docs/audits/main-submission-observer-native-feature-gap-repair-2026-10-15.md.
REVIEWED_NATIVE_FEATURE_GAP_OBSERVER_SOURCES = {
    'src/engine/monitoring/submission_bottleneck_monitor.py': (
        '90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d',
        'c241bc4e58f9025229fb7abce51475a1b6ec4b4c2c79c54e6a35fa53cfb98236',
    ),
}


# Scope-bound raw/selected ready census; no machine/provider admission.
# Review: docs/audits/main-entry-price-progress-deployment-review-2026-10-15.md.
REVIEWED_SCOPE_READY_OBSERVER_SOURCES = {
    'src/engine/monitoring/submission_bottleneck_monitor.py': (
        '90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d',
        '203b397835edf5ff0d578aa8d5b25126f8c61307adbe92031371b9000d710e56',
    ),
}

# Snapshot-only holding observer concurrency repair. Preserve the original
# PREOPEN contract and every execution gate; bind only these reviewed bytes.
# Evidence: docs/audits/main-holding-context-dictionary-race-repair-2026-10-15.md.
REVIEWED_HOLDING_CONTEXT_SNAPSHOT_SOURCES = {
    'src/engine/sniper_state_handlers.py': (
        'b87f2ecdd7ef43a9f5268e06a5a9fbf8991223acffd58c3258aec68d77832500',
        '92f4c9380e4bd5caec8f252bbb8deb4f3012de1031ec5d37389c430623efde8d',
    ),
}

# Exact carried-stop source snapshot repair. Publication and consumed sources
# retain strict immutable validation; native future-only appends are locked.
# Evidence: docs/audits/main-finalization-live-vote-read-race-repair-2026-10-15.md.
REVIEWED_STOP_VOTE_SNAPSHOT_SOURCES = {
    'src/engine/automation/main_stop_postclose.py': (
        '360573dc170d91617cbaec7f1c8713b769c403b22e52449e11434019360a6224',
        'e9ab07117a0200610e19f4b24ea0000579203628a887e16387b24189b8734a13',
    ),
}

# Preserve the frozen predecessor while ordered startup has not completed.
# The producer defers publication; detector deadlines and failures stay strict.
REVIEWED_ORDERED_PUBLICATION_SOURCES = {
    'src/engine/monitoring/submission_bottleneck_monitor.py': (
        '90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d',
        '182e0a4b73b18536a7acdfe6aef36c88d7a9d919ca0647e6646df9f4c0569456',
    ),
}

# Approved e6326b0b1: classify local opportunity custody without changing the
# preserved policy, provider failure counters or retry/order authority.
# Evidence: docs/audits/main-premarket-error-repair-and-restart-2026-10-15.md.
REVIEWED_OPPORTUNITY_CUSTODY_SOURCES = {
    'src/engine/ai_engine_openai.py': (
        '58aa3ca78af08ef2cac6ec0501cc212947c4c5fa743c58b2daea26c0ba205937',
        '9731f7d729506494fc088ed74dcd54d7f5daa96604364dcac55131bf53a0cc32',
    ),
}

# Preserve original async identity on early non-provider receipts. Exact bytes;
# no request/deadline renewal, provider admission or policy-selection change.
# Evidence: docs/audits/main-entry-price-progress-deployment-review-2026-10-15.md.
REVIEWED_ENTRY_RECEIPT_IDENTITY_SOURCES = {
    'src/engine/ai_engine_openai.py': (
        '58aa3ca78af08ef2cac6ec0501cc212947c4c5fa743c58b2daea26c0ba205937',
        'e75c946a70ec6513162c5a657604830a82e4d718bd5400076d0e05a1639e56f6',
    ),
}

# Original result custody across a fixed-watch session boundary. Route conflict
# remains nonexecution; no fallback route, new request or deadline is admitted.
REVIEWED_ASYNC_SESSION_BOUNDARY_SOURCES = {
    'src/engine/sniper_state_handlers.py': (
        'b87f2ecdd7ef43a9f5268e06a5a9fbf8991223acffd58c3258aec68d77832500',
        'c3ac7e88532734dcd14c1037ecaecea82064701c3a6cc03ae1871e158bc38f80',
    ),
}

# Bind the live KST terminal decision/receipt and exclude proven manual custody
# only when no order or reconciliation is pending. No historical HOLD is inferred.
# Evidence: docs/audits/main-entry-price-progress-deployment-review-2026-10-15.md.
REVIEWED_TERMINAL_CLOCK_CUSTODY_SOURCES = {
    'src/engine/sniper_state_handlers.py': (
        'b87f2ecdd7ef43a9f5268e06a5a9fbf8991223acffd58c3258aec68d77832500',
        'bb6108b506bebfb957f7257bbf4e466837f19a48eff6a742a245f5c3b3e57dcf',
    ),
}


# Exact PREOPEN-to-candidate arm cleanup, with unchanged original deadlines and
# policy/source custody. This is a code check, not selection/startup authority.
# Evidence: docs/audits/main-native-entry-arm-handoff-repair-2026-10-15.md.
REVIEWED_NATIVE_ARM_COMPLETION_SOURCES = {
    'src/engine/sniper_state_handlers.py': (
        'b87f2ecdd7ef43a9f5268e06a5a9fbf8991223acffd58c3258aec68d77832500',
        '93285e4678038c07e56b34187dc4a9b4ba7b6ee70c380a32f18eaf622fd57335',
    ),
}


# Carried policy readers exclude only later, never-consumed observation tails.
# Exact reviewed source bytes; full research and numeric selection stay strict.
REVIEWED_CARRIED_SOURCE_BINDING_SOURCES = {
    # Preserve a previous PID's delay incident after current native proof.
    'src/engine/monitoring/submission_bottleneck_monitor.py': (
        '90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d',
        '2f897e3b30c912faba4a96bc4482bd23cd404d70e2ae7fc3593d4492d2395ca4'),
    # Operator-approved 40b931254: long-probe allocation and exact Main weak-veto scope.
    'src/engine/sniper_state_handlers.py': (
        'b87f2ecdd7ef43a9f5268e06a5a9fbf8991223acffd58c3258aec68d77832500',
        '493b9802652ac820803a5887e7e5670f7bbe8b42d000547abf3f45df06479563'),
    'src/engine/automation/main_stop_postclose.py': (
        '360573dc170d91617cbaec7f1c8713b769c403b22e52449e11434019360a6224',
        '72334470389eed899eed84da5fb3d157bd8ae6078e2d38bfb10b0bc96b79ba6f'),
}


# Exact reviewed HPSP replay/receipt and 06deaab source-recovery code.
# Policy values, sources and all execution guards remain independently checked.
REVIEWED_HPSP_SOURCE_RECOVERY_SOURCES = {'src/engine/sniper_state_handlers.py': ('b87f2ecdd7ef43a9f5268e06a5a9fbf8991223acffd58c3258aec68d77832500', 'f19298ecdebfe6bb936c8d3700c50073592da6bdd1548dc104bfc9595399023d'), 'src/engine/sniper_execution_receipts.py': ('97ca5efc27896fb31cf04eeccf596efe389e41b2332907b36039357e3f77472c', 'dc4a57286b38f72c96e538e7eb3851f806af1b9c07e0145f3f5aed51ea00bbe1'), 'src/engine/scalping/trailing_mechanical_strength.py': ('b2c425e1fff3f8241b9fd5b55c590eeb264b0a1ab909b0059bc32198e6ad6c1a', '6e6ff97542868f4624efb18e8b31c1fab6142b37921b98e67f1ace614e79ceb3'), 'src/engine/scalping/trailing_mechanical_replay.py': ('78d8f61e0105818402608bff314bfb11f70850a8701812ab0ddce1cdf9274895', 'de989aadd577f78f298677d10b6054fb4e11530af6920ba9f0841212c47ddfe2')}


# Reviewed preset/cost-clock/manual-handoff observations; original policies stay sealed.
REVIEWED_HOLDING_CONTRACT_SOURCES = {'src/engine/sniper_state_handlers.py': ('b87f2ecdd7ef43a9f5268e06a5a9fbf8991223acffd58c3258aec68d77832500', '8eaa7493ce235c64e8ccea966afee2a87ef6ee201dd080407584b51925d45ec2'), 'src/engine/scalping/main_stop_policy.py': ('c444f74e9da0339b564543322da389bcbe38552c4ed56531e8ebf5c21676752e', '8cdd21315d3d0db00f3383406dbb7d885ca02fef7ed957edf4f9535f0f022087'), 'src/engine/scalping/main_stop_replay.py': ('f609161b46296329cb08a4f4b71a07f465f6e412429286348901d85e66c90363', '3194cc743fc664176245ccb5ffbb26469d68c4276bc8c86aa4d0d87377615ffe'), 'src/engine/automation/main_stop_postclose.py': ('360573dc170d91617cbaec7f1c8713b769c403b22e52449e11434019360a6224', '0a33ccf900e7d512ff03ee62923efa95842ea87caeb2987fbd1b479aa18f8258'), 'src/engine/automation/main_stop_source_index.py': ('ddaab50afeee7a47c4a49565f27dc699532aabf8197e5276eb0d57cf974dfdce', '802a8f3878f5d9d2fd299c79a57f9b84db6bf1de52017f0e995958b65145381d')}


# Reviewed full-byte pair for one-pass source verification only. Qualification,
# selection, policy values and the original native source proof are unchanged.
# Evidence: main-postclose-read-reduction-deployment-review-2026-10-16.md.
REVIEWED_POSTCLOSE_READ_SOURCES = {
    'src/engine/scalping/pre_submit_delay_initial_policy.py': (
        'ea2f93040975dcf7b9fc247ad57c706fd2bab6a9b717da7f754a0364e43dccf0',
        '037af000399c501362c62a63e4361501c041e3db0289b1edd059b839e36e0a47',
    ),
}

# Carried stop dependency prefixes remain byte-sealed across later native rows.
REVIEWED_CARRIED_VOTE_PREFIX_SOURCES = {
    'src/engine/automation/main_stop_postclose.py': (
        'e9ab07117a0200610e19f4b24ea0000579203628a887e16387b24189b8734a13',
        'cce1f797bd17f5ddde0aa5eec68cdb285c224e198fea7bb184d03a444ff32c05',
    ),
}

# Completed overnight SELL receipts use their sealed broker/BUY identity only.
REVIEWED_OVERNIGHT_SELL_RECEIPT_SOURCES = {
    'src/engine/error_detector.py': (
        '6da85a87a0d32d2a2815ee452353394afc2abaeac009084d1f69aa1d2934f875',
        '96c4218b76cd19310afc3d089a1fc6ff0e80a2b0c45316e546600ca6a5d9fb77',
    ),
    'src/engine/holding_exit_observation_report.py': (
        '2ec0a7be672eb04044a9094b7ee445af66cef17720df83efe24e6148110ded03',
        'da364a9f0a6933158e95046f82e7669f0609244c51cd8f35e119949cc0bc0969',
    ),
    'src/engine/scalping/ai_decision_trace.py': (
        'de1eb13ce98abe99980a387e87ab852764d6a4b8f94a24c0c1540234d6e478f4',
        '4ca36bfcf257cb8dc39738cff5e71b3da32f458e8e9febabc31f4acef1277bc4',
    ),
    'src/engine/scalping/continuous_reversal_policy.py': (
        '3522757d44f2cb9201892757dc40a0a9650e2c962709d15b2f7b99b737987627',
        '2c83f7afad5355cda14ef76eb82793ffb1cb982d4e158d260aa71d3c4f1c6cbd',
    ),
    'src/engine/scalping/continuous_reversal_policy_v2.py': (
        '1ccf5f2ab3bca1e5f6fbb09d7173979fe48f0019ae1aed8e95df279dcd47fad8',
        'bdee85eff700fae45e0725066180b3336985fec25af49819d01928ccfe06d4c6',
    ),
    'src/engine/scalping/continuous_reversal_policy_v3.py': (
        '905232875ec6767cb4169fd9c8935ccf800f05fa7e3316687398518cae54f0fb',
        '86b942fa51b2079fb9b51df50f8da92e9b92d0fdab4d397ca7f297abe453399b',
    ),
    'src/engine/scalping/continuous_reversal_policy_v4.py': (
        'f37709fb11b2b13006b268c401541749d18e8845de16174b9b6736dfd16ea3d4',
        '9b1e7ba3fefb6df1c6dc20a0c336f30b006ce982f38764c819a91f5e3f091e4f',
    ),
    'src/engine/scalping/continuous_reversal_policy_v5.py': (
        '1d60a547a5730ff34da9c144a14feedfa322e09604bde84a46aafd04999941f6',
        'b222050e81150a95751bcb7f4614e61dadc3ded1232bc76cae81b010b3a7c1e7',
    ),
    'src/engine/scalping/continuous_reversal_policy_v6.py': (
        '568c46b69d35a9c6d4ab03ab92b10c609c711cd311706508e287e1d1431f81f7',
        'd669d8831add3b2a62d51e0e2c98baa7e6eb8e45d45f574d75883fb260cec273',
    ),
    'src/engine/scalping/mechanistic_entry_runtime_policy.py': (
        '671f655287ff452f4dc5162c754c98a9e05e9397eb2a9e217f34fc193db1104d',
        '215ac04e8c50c5d18777617b262c7a73b77c2d4d134c26c6f4c88a31dc162867',
    ),
    'src/engine/scalping/reversal_code_handoff.py': (
        'f73faae0d4eb1e4f844d2cc7b6ab27f0c03316cb6d2aa85a8dbbae44e43c9fec',
        '5fc405a276c114e9ac6966b3d56b662863a5e01ccc4bb61c133db916f9448ab9',
    ),
    'src/engine/scalping/reversal_source_diagnostics.py': (
        'f3d66158bbeae90f8258333d90efb45e652ca95d6b4ef5f868066e0509c18783',
        'bf7dd538048888ce9793ccdf39a6c5c4a463c9e3379f4c3c5c1a09173f543eb8',
    ),
    'src/engine/sniper_execution_receipts.py': (
        'dc4a57286b38f72c96e538e7eb3851f806af1b9c07e0145f3f5aed51ea00bbe1',
        '14faf52dc561d6f0f3f859cae9ea2ec69a7d9dc298f7ddda691bb2e665654880',
    ),
    'src/engine/sniper_post_sell_feedback.py': (
        '8b6d50ce6c5693338942fcbfeeb397d8ac13f244188cc6a8ec50229c19efe501',
        '8fcbf7de95acc2e5ba3121be0f20ece3bbefc7bd22fb57cc4cebe938115fc2d9',
    ),
    'src/engine/sniper_trade_review_report.py': (
        '5267041fe305ab93d636e3fe27f6633c86bddd49f7250418c2898ca55706cefd',
        'fd08e8db61295786759280e46ddaa4d8198a04053d6c702495a26cee76346c39',
    ),
    'src/engine/scalping/pre_submit_delay_initial_policy.py': (
        'ea2f93040975dcf7b9fc247ad57c706fd2bab6a9b717da7f754a0364e43dccf0',
        '74adf3c630fa6ed24819f371007faa8f8b4ee086c330be2cd8431cfe89af4c52',
    ),
    'src/engine/scalping/pre_submit_delay_tuning.py': (
        'c577f885ca02eef999aad71f514fa7a4ef4f7f13e328c0614e93e46b5be6f810',
        'e677004513e6c3b5382ea58933aa39e12feac9dcfafbdd93b88dda53e173bf76',
    ),
    'src/engine/automation/runtime_policy_bootstrap.py': (
        '7a2e67d6d537ccc0a322bbbde8935f96de74869bc48e456bd13071225dd84b56',
        '1dcbb457a66330ff9285574c2182b146aa4663ac171358249df7571ee6be2b6a',
    ),
    'src/engine/infrastructure/validation_digest_session.py': (
        '8fc28395c82a3efa15896c21362d3be7162656fec506fbba6f939e8c6b5101a3',
        'bfdcbf093652783bea5d2c72bf10e1dc910b5d3cdca9c702279ee75a15ec77b9',
    ),
    'src/engine/scalping/initial_quantity_policy.py': (
        'b00edf437d65017bdf10760bac8ebf1a4f603e0a45b6ccc0d32159d5e73985d2',
        'b05fdfdd1f2bb0560c8af33c08d6aa046791d46db90a3b56b5eb2e9d7bbeb326',
    ),
}

# Warning-only health for proven preassessment traces with lazy journals absent.
REVIEWED_PREASSESSMENT_OBSERVER_SOURCES = {
    'src/engine/monitoring/submission_bottleneck_monitor.py': (
        '203b397835edf5ff0d578aa8d5b25126f8c61307adbe92031371b9000d710e56',
        'a1284490d780a882b8c7591765ccf5f081b53cf9320fe350d03b620263310e55',
    ),
}


# Exact reviewed source-gap/crossing repair; fresh capability fixtures remain required.
# Review: docs/audits/main-postclose-source-gap-final-release-review-2026-10-16.md.
REVIEWED_SOURCE_GAP_CROSSING_SOURCES = {
    'src/engine/ai/holding_exit_vote.py': ('05ba419f5affd9f8b329d3719e77cfcf5f3b4c73ac7496ba15336d76faa340c6', '8d97be85f1d1e0a5cc1408d1060cd2c43a8014be9456ae10b4251431b190ee6a'),
    'src/engine/ai/holding_vote_replay_source.py': ('0d67dab01f0cf1d5ef4657659ab433d892d854ecb6e9a656a5d93b2e439ff7cf', '6362843a02931562326ce6d700e25dfc3cb2588c42479edbe204ac2aeadf677f'),
    'src/engine/ai_engine_openai.py': ('e75c946a70ec6513162c5a657604830a82e4d718bd5400076d0e05a1639e56f6', '61d3cfc4e8bca5348ee2816b5451d294e7d825e2f78fe3d134f4ef30c3bdeb5c'),
    'src/engine/automation/entry_cancel_wait_tuning.py': ('5bdf8f81db148490457f2ab36a9f2c1c6fe6a300b7f5ef9f1d720a91bc44491a', '8313bcfc096d43dbc62d3e4e5938d1ddd47ef1127e6131aae88b160e3736938e'),
    'src/engine/automation/main_stop_source_index.py': ('802a8f3878f5d9d2fd299c79a57f9b84db6bf1de52017f0e995958b65145381d', '791fd757311aa8c0a96b2373165a52a560b026492992e46e9fe386996eb605ff'),
    'src/engine/scalping/ai_decision_quality.py': ('218b2d1ed9133ed11894d729d27afdef4288b712262811d6c13e6a1fa013e34f', 'd64bd9fcc77969b326d0ac12938a50ae84b7ad5bf27af113530ce21253b8787f'),
    'src/engine/scalping/entry_cancel_wait_runtime.py': ('32dfb19821fb2df08a51da16cc158625c53e468f0cd63a4b5930c321b37e9e0e', '8c4871d3064e36d8a57e581bac1ce0b4122325e5f5a2365739f8118adc633b4e'),
    'src/engine/scalping/entry_split_order_plan.py': ('ed738295a7de91c3972c8360b655d222b26f69e4d1976b2ef27c2c0f0e660c5c', 'bf3c8b69f4c92270f8084bbb44373aa213af1dc94da22d91cf4cbd23e300d37f'),
    'src/engine/scalping/holding_profit_exit_semantics.py': ('0815edbd37d2932ec57337fe579f5576ffce2fc2140c5273cbdcf26589268454', '7512700df7e7d3bf705ec3e5d866bf9b916e564d60312fa3918f950c34431b78'),
    'src/engine/scalping/main_stop_policy.py': ('8cdd21315d3d0db00f3383406dbb7d885ca02fef7ed957edf4f9535f0f022087', 'a5faea8355cc607e795df2a7f6bf48c385ca509579240a9e23589ec41fa435ad'),
    'src/engine/scalping/main_stop_replay.py': ('3194cc743fc664176245ccb5ffbb26469d68c4276bc8c86aa4d0d87377615ffe', 'a9351c17a3b9a7cd84a4be7c6672a801ff77f2c537459d95a9eb18b4eca6ff15'),
    'src/engine/sniper_state_handlers.py': ('bb6108b506bebfb957f7257bbf4e466837f19a48eff6a742a245f5c3b3e57dcf', '706a7dccde4559254bb9ec2d4bb860fed1bf15c8b7d7c9b2b36103da8c3d797f'),
    'src/engine/sniper_trade_review_report.py': ('5267041fe305ab93d636e3fe27f6633c86bddd49f7250418c2898ca55706cefd', 'b513734f2fe58503f916ff1a513875faf72b75e64cd5fb07c87c68d7b8e61c66'),
}


# Exact reviewed probe partial custody and native WS adoption consumer bytes.
# Review: docs/audits/main-probe-partial-integrated-deployment-review-2026-10-16.md.
REVIEWED_PROBE_PARTIAL_INTEGRATION_SOURCES = {'src/engine/sniper_state_handlers.py': ('bb6108b506bebfb957f7257bbf4e466837f19a48eff6a742a245f5c3b3e57dcf', '81a29f9f19090487a48983120f9395e29565603c108d42481915b9ca3b0ab35c'), 'src/engine/sniper_execution_receipts.py': ('dc4a57286b38f72c96e538e7eb3851f806af1b9c07e0145f3f5aed51ea00bbe1', 'c6e5a208c32165ca112b5f33643494030df79302680e4b93f316a91696d7e7a1'), 'src/engine/kiwoom_sniper_v2.py': ('bb8cc6f224428a073f60826f8aa70e97d4b68b0383c907d681b8be5473a2d7c6', 'e1f43d4d08a0606db678c59f5755b94fbb976ef4ce55ece812ecc00e97c8973e'), 'src/engine/kiwoom_websocket.py': ('e60b5435694e74fc9afa65101b4b407af4da365d07dbac0b38263c66bf8e8921', '9aca69dc06a8fffee8999d8c8c2cdece1760e9fdb21e3c8eddf8cda87a6da9e2')}



# Exact source pairs reviewed in long4-source-retention-integration-review-2026-10-16.md.
REVIEWED_LONG4_SOURCE_RETENTION_SOURCES = {'src/engine/ai/holding_exit_vote.py': ('05ba419f5affd9f8b329d3719e77cfcf5f3b4c73ac7496ba15336d76faa340c6', '9d516e9dd068613765944d7ab78d65fe561905046c38d45c0d0a835078d98a7b'), 'src/engine/ai/holding_vote_replay_source.py': ('0d67dab01f0cf1d5ef4657659ab433d892d854ecb6e9a656a5d93b2e439ff7cf', '6aa1db742f4f2354c17ed9bd24cfb1bcfaace5e0130a8d0dceef84343ea6a428'), 'src/engine/ai_engine_openai.py': ('e75c946a70ec6513162c5a657604830a82e4d718bd5400076d0e05a1639e56f6', '32ad96c3959cfbc934716a2af3d62f9ef2989a6ae3b3a30e3426be2d1fe7c75f'), 'src/engine/automation/main_stop_postclose.py': ('e9ab07117a0200610e19f4b24ea0000579203628a887e16387b24189b8734a13', 'c3aa703f54661aeae94143fb36afd2d2ac7a4337c1ba346062c21ca2be12a9cc'), 'src/engine/automation/main_stop_source_index.py': ('802a8f3878f5d9d2fd299c79a57f9b84db6bf1de52017f0e995958b65145381d', '791fd757311aa8c0a96b2373165a52a560b026492992e46e9fe386996eb605ff'), 'src/engine/automation/runtime_policy_bootstrap.py': ('7a2e67d6d537ccc0a322bbbde8935f96de74869bc48e456bd13071225dd84b56', '1dcbb457a66330ff9285574c2182b146aa4663ac171358249df7571ee6be2b6a'), 'src/engine/holding_exit_observation_report.py': ('2ec0a7be672eb04044a9094b7ee445af66cef17720df83efe24e6148110ded03', 'd9310a1136cc2086e83037c020d5d44a9d3b3f57d1207697bcd8eac8f6cf73fe'), 'src/engine/kiwoom_sniper_v2.py': ('bb8cc6f224428a073f60826f8aa70e97d4b68b0383c907d681b8be5473a2d7c6', 'e1f43d4d08a0606db678c59f5755b94fbb976ef4ce55ece812ecc00e97c8973e'), 'src/engine/monitoring/submission_bottleneck_monitor.py': ('203b397835edf5ff0d578aa8d5b25126f8c61307adbe92031371b9000d710e56', '1588764df3b3bdedd628d860d832c2ac950171a3928719f4f780ed4a80840ea2'), 'src/engine/scalping/continuous_reversal_policy.py': ('3522757d44f2cb9201892757dc40a0a9650e2c962709d15b2f7b99b737987627', '2c83f7afad5355cda14ef76eb82793ffb1cb982d4e158d260aa71d3c4f1c6cbd'), 'src/engine/scalping/holding_path_vote_policy.py': ('80950db0e9d7420a29cd9ea2b6c6b1b620227a5e13a6e1929c2361b92eb53ab6', '6b739dcdfac2614712e03eb74fb4afeec99cefa28946537c507efc5cc1e5895a'), 'src/engine/scalping/holding_path_vote_replay.py': ('886860aa6181bafb08d5151c4ac1ff0ca5ed6df575cab13e33a0b455cf06366a', 'cd700be6898f87860182379c768cb2960eb79186b187a27e2ed610707924a7cd'), 'src/engine/scalping/main_stop_policy.py': ('8cdd21315d3d0db00f3383406dbb7d885ca02fef7ed957edf4f9535f0f022087', 'a5faea8355cc607e795df2a7f6bf48c385ca509579240a9e23589ec41fa435ad'), 'src/engine/scalping/main_stop_replay.py': ('3194cc743fc664176245ccb5ffbb26469d68c4276bc8c86aa4d0d87377615ffe', 'a9351c17a3b9a7cd84a4be7c6672a801ff77f2c537459d95a9eb18b4eca6ff15'), 'src/engine/scalping/pre_submit_delay_initial_policy.py': ('ea2f93040975dcf7b9fc247ad57c706fd2bab6a9b717da7f754a0364e43dccf0', '74adf3c630fa6ed24819f371007faa8f8b4ee086c330be2cd8431cfe89af4c52'), 'src/engine/scalping/pre_submit_delay_tuning.py': ('c577f885ca02eef999aad71f514fa7a4ef4f7f13e328c0614e93e46b5be6f810', 'e677004513e6c3b5382ea58933aa39e12feac9dcfafbdd93b88dda53e173bf76'), 'src/engine/sniper_execution_receipts.py': ('dc4a57286b38f72c96e538e7eb3851f806af1b9c07e0145f3f5aed51ea00bbe1', '179948c3eb4a0bd7bab6d121ae6d90a0817b82dbef557dea72a25db62c0b8e05'), 'src/engine/sniper_state_handlers.py': ('bb6108b506bebfb957f7257bbf4e466837f19a48eff6a742a245f5c3b3e57dcf', 'f0277cdfb0e2de299d725afc0d047a6c21aa4ec0608d7139e357dba5eb3be459')}

# Exact reviewed delay source/zero-cell/observer repair. The two added
# dependencies did not belong to the incumbent delay contract; their exact
# candidate bytes are verified independently without changing its old digest.
# Evidence: docs/audits/pre-submit-semantic-implementation-review-2026-10-16.md.
REVIEWED_DELAY_SITUATION_SOURCES = {'src/engine/automation/pre_submit_delay_partitioned_research.py': ('ad5186b7058a1cf7aeefa099cb59e3b03ae51cca7fc26be0e021d90c8e721bdc',
                                                                    '1f92ea9be98b4a9d0cce66d4105959b21eb03b5d060c501d628b9cef2cc73d65'),
 'src/engine/automation/pre_submit_delay_source_ledger.py': ('8b97e228f167eebcf9e6009325d73f1507e1e00eedf53d21985af64b6e8701f7',
                                                             '8d6a8b3d66af66bba270ba835016403e1740bba16ae374133efb9c3efa681ef0'),
 'src/engine/monitoring/submission_bottleneck_monitor.py': ('203b397835edf5ff0d578aa8d5b25126f8c61307adbe92031371b9000d710e56',
                                                            'b0b3ddc61584f4cfce9890ab97a90160f941ebcf024188f5de4aac316418bb33'),
 'src/engine/scalping/pre_submit_delay_initial_policy.py': ('ea2f93040975dcf7b9fc247ad57c706fd2bab6a9b717da7f754a0364e43dccf0',
                                                            '9bf1914b5445ad687d2480352cb01d6ca3ab742709175a3ba7181d1747499edc'),
 'src/engine/scalping/pre_submit_delay_observation.py': ('909104c8623dd6219ba0a1cb2b964e8998e5eb52a9bae834db26e9f2cb55a0fa',
                                                         '5128d73f6d45777c5671fd26a774dae5d4839203035607b5bb53a9bcc860e964'),
 'src/engine/scalping/pre_submit_delay_tuning.py': ('c577f885ca02eef999aad71f514fa7a4ef4f7f13e328c0614e93e46b5be6f810',
                                                    'c2fb791a41e35c326ca874562c332fac0e7ea16cda0066fc82f34679cd93ef1a'),
 'src/engine/sniper_state_handlers.py': ('bb6108b506bebfb957f7257bbf4e466837f19a48eff6a742a245f5c3b3e57dcf',
                                         '4a2545b9d796aab6c9df68f08e57ea5f681a856395cde272a613ddea977d7258')}
REVIEWED_DELAY_CONTRACT_EXTENSIONS = {('23a13aba62884a5d3a0d48a3f91ebff4262571f6', 'afb82ed5c746f939e20ea2a7df7dda595b6091f61e46ca2d1ad3e308c1db73bc'): {'src/engine/automation/pre_submit_delay_situation_projection.py': 'c77e565c1f29b64551e690f0e0901226c73baba2c53a61b6c49239be76c39f28',
                                                                                                                    'src/engine/scalping/reversal_extended_catalog.py': 'c03dddde3e642bfa9be01c130eabfcfcc420a182108411099339944c594d4f95'}}


# Exact original-policy to reviewed source continuity/control-evidence consumer bytes.
REVIEWED_NONFIXED_CONTINUITY_SOURCES = {'src/engine/kiwoom_sniper_v2.py': ('bb8cc6f224428a073f60826f8aa70e97d4b68b0383c907d681b8be5473a2d7c6',
                                    '3b35fc7133fc87cf5b23ae6f03c3272b9b78b61840f3bc1c6f0e84db5ba8def4'),
 'src/engine/monitoring/submission_bottleneck_monitor.py': ('203b397835edf5ff0d578aa8d5b25126f8c61307adbe92031371b9000d710e56',
                                                            '2b8af49c0dca2527dd6ab9caea3d8e9e5e98eb73a7f8e069836934d88446ecb6'),
 'src/engine/sniper_state_handlers.py': ('bb6108b506bebfb957f7257bbf4e466837f19a48eff6a742a245f5c3b3e57dcf',
                                         'b18c9204588e52239be3d9167c42fd2ff74855a9244dbb1acd1c36dc78d25fe5')}

# Exact report-only as-of retention repair, reviewed with the actual 118 rows.
# Review: docs/audits/main-source-cursor-and-auxiliary-integration-review-2026-10-16.md.
REVIEWED_CURSOR_ASOF_SOURCES = {
    'src/engine/monitoring/submission_bottleneck_monitor.py': (
        '203b397835edf5ff0d578aa8d5b25126f8c61307adbe92031371b9000d710e56',
        '082d6e1af5276405fc493d2be739818ad7d9d55e5026a113029f66eaec0b4b2e',
    ),
}


# Exact prepared 10/19 origin to the reviewed quote-delivery consumer bytes.
# No numeric policy, provider or order authority changes cross this boundary.
REVIEWED_NONFIXED_QUOTE_DELIVERY_SOURCES = {
    'src/engine/ai_engine_openai.py': (
        'b5c8b6e262678c5354ced1fd30ae4d20b974e50fbb01187b4ab2a9df61a010d7',
        'fb228f284ff0898c1f260149b653d03c71f8f17f1544fe5bf46cc0aa396c0cc4'),
    'src/engine/sniper_state_handlers.py': (
        '669b6109e36f81e9dee263d1c3e31011d55fd612d5641713c6ee109a827a9425',
        'bc7885265ca7f0f59d2fec49eb56c114d7759b641f68fa80d3285fe9f48429e0'),
}


def _verify_entry_code_delta(root, commit, origin, paths, expected):
    """Read-only code projection shared by pre-stop and selected handoff checks."""
    import ast
    root = Path(root)
    allowed = {
        # Report-only lifecycle classification; delay qualification/selection
        # and every other monitor function remain byte/AST bound.
        'src/engine/monitoring/submission_bottleneck_monitor.py': {'_reversal_lifecycle_diagnostic'},
        'src/engine/ai_engine_openai.py': {'_final_entry_machine_inputs'},
        'src/engine/sniper_state_handlers.py': {'_resolve_watching_state_change_refresh', '_get_live_entry_arm'},
        'src/engine/scalping/pre_submit_delay_tuning.py': {'_verify_runtime_code_contract', 'prepare_runtime_policy'},
        'src/engine/automation/runtime_policy_bootstrap.py': {'_pre_submit_delay_handoff'},
        'src/engine/scalping/holding_vote_experiment.py': {'_code_paths', 'code_sha'},
        'src/engine/scalping/holding_path_vote_policy.py': {'validate_successor', 'verify_source_handoff'},
    }
    def revision_bytes(revision, name):
        try:
            return subprocess.check_output(['git', '-C', str(root), 'show', revision + ':' + name],
                                           stderr=subprocess.DEVNULL, timeout=10)
        except (OSError, subprocess.SubprocessError) as exc:
            raise ValueError('entry_consumer_code_source_missing') from exc
    own_name = 'src/engine/automation/intraday_release_handoff.py'
    if (root / own_name).read_bytes() != revision_bytes(commit, own_name):
        raise ValueError('entry_consumer_dirty_verifier')
    original_hashes, changed = {}, []
    extensions = REVIEWED_DELAY_CONTRACT_EXTENSIONS.get((origin, expected), {})
    for key, name in paths.items():
        after = (root / name).read_bytes()
        if name in extensions:
            if hashlib.sha256(after).hexdigest() != extensions[name] or after != revision_bytes(commit, name):
                raise ValueError('entry_consumer_contract_extension_unreviewed:' + name)
            changed.append(name)
            continue
        before = revision_bytes(origin, name)
        if after != revision_bytes(commit, name):
            raise ValueError('entry_consumer_dirty_release')
        original_hashes[key] = hashlib.sha256(before).hexdigest()
        if before == after:
            continue
        pair = (hashlib.sha256(before).hexdigest(), hashlib.sha256(after).hexdigest())
        if pair in (REVIEWED_NONFIXED_QUOTE_DELIVERY_SOURCES.get(name),
                    REVIEWED_CURSOR_ASOF_SOURCES.get(name),
                    REVIEWED_NONFIXED_CONTINUITY_SOURCES.get(name),
                    REVIEWED_DELAY_SITUATION_SOURCES.get(name),
                    REVIEWED_LONG4_SOURCE_RETENTION_SOURCES.get(name),
                    REVIEWED_PROBE_PARTIAL_INTEGRATION_SOURCES.get(name),
                    REVIEWED_SOURCE_GAP_CROSSING_SOURCES.get(name),
                    REVIEWED_ENTRY_CONSUMER_SOURCES.get(name),
                    REVIEWED_ENTRY_LATENCY_SOURCES.get(name),
                    REVIEWED_ENTRY_BOUNDARY_SOURCES.get(name),
                    REVIEWED_ENTRY_RESPONSE_SOURCES.get(name),
                    REVIEWED_ENTRY_STORAGE_SOURCES.get(name),
                    REVIEWED_JOINT_CONSUMER_SOURCES.get(name),
                    REVIEWED_REST_REDUCTION_SOURCES.get(name),
                    REVIEWED_IO_OBSERVER_SOURCES.get(name),
                    REVIEWED_IO_DIGEST_SOURCES.get(name),
                    REVIEWED_STOP_CONSUMER_SOURCES.get(name),
                    REVIEWED_NONFIXED_SUBMIT_SOURCES.get(name),
                    REVIEWED_ENTRY_PROJECTION_DELIVERY_SOURCES.get(name),
                    REVIEWED_ENTRY_PROJECTION_MOUNT_SOURCES.get(name),
                    REVIEWED_STARTUP_OBSERVER_SOURCES.get(name),
                    REVIEWED_OBSERVER_HEALTH_SOURCES.get(name),
                    REVIEWED_SUBMISSION_TIMEOUT_SOURCES.get(name),
                    REVIEWED_OBSERVER_TERMINAL_SESSION_SOURCES.get(name),
                    REVIEWED_PREMARKET_OBSERVER_SOURCES.get(name),
                    REVIEWED_ACTIVE_OBSERVER_SOURCES.get(name),
                    REVIEWED_CURRENT_OBSERVER_SOURCES.get(name),
                    REVIEWED_NATIVE_HANDOFF_INTEGRATION_SOURCES.get(name),
                    REVIEWED_OBSERVER_STATE_READER_SOURCES.get(name),
                    REVIEWED_NATIVE_INCOMPLETE_OBSERVER_SOURCES.get(name),
                    REVIEWED_NATIVE_FEATURE_GAP_OBSERVER_SOURCES.get(name),
                    REVIEWED_SCOPE_READY_OBSERVER_SOURCES.get(name),
                    REVIEWED_HOLDING_CONTEXT_SNAPSHOT_SOURCES.get(name),
                    REVIEWED_STOP_VOTE_SNAPSHOT_SOURCES.get(name),
                    REVIEWED_ORDERED_PUBLICATION_SOURCES.get(name),
                    REVIEWED_OPPORTUNITY_CUSTODY_SOURCES.get(name),
                    REVIEWED_ENTRY_RECEIPT_IDENTITY_SOURCES.get(name),
                    REVIEWED_ASYNC_SESSION_BOUNDARY_SOURCES.get(name),
                    REVIEWED_TERMINAL_CLOCK_CUSTODY_SOURCES.get(name),
                    REVIEWED_NATIVE_ARM_COMPLETION_SOURCES.get(name),
                    REVIEWED_CARRIED_SOURCE_BINDING_SOURCES.get(name),
                    REVIEWED_HPSP_SOURCE_RECOVERY_SOURCES.get(name),
                    REVIEWED_HOLDING_CONTRACT_SOURCES.get(name),
                    REVIEWED_POSTCLOSE_READ_SOURCES.get(name),
                    REVIEWED_CARRIED_VOTE_PREFIX_SOURCES.get(name),
                    REVIEWED_OVERNIGHT_SELL_RECEIPT_SOURCES.get(name),
                    REVIEWED_PREASSESSMENT_OBSERVER_SOURCES.get(name)):
            changed.append(name)
            continue
        if name not in allowed:
            raise ValueError('entry_consumer_producer_changed:' + name)
        def projection(raw):
            tree = ast.parse(raw)
            tree.body = [node for node in tree.body if not (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in allowed[name])]
            return ast.dump(tree, include_attributes=False)
        if projection(before) != projection(after):
            raise ValueError('entry_consumer_unreviewed_change:' + name)
        changed.append(name)
    original_digest = hashlib.sha256(json.dumps(original_hashes, sort_keys=True,
        separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii')).hexdigest()
    if original_digest != expected:
        raise ValueError('entry_consumer_original_code_contract_invalid')
    return changed


def verify_candidate_delay_code(day, root, commit):
    """Reject an incompatible delay consumer before the running Main is drained.

    This does not select the candidate, publish receipts or authorize startup;
    the normal custody and full bootstrap checks still run after selection.
    The ordered caller verifies the incumbent bootstrap first.
    """
    _today(day, None)
    root = Path(root).resolve(strict=True)
    if Path(__file__).resolve().parents[3] != root:
        raise ValueError('entry_consumer_candidate_code_mismatch')
    manifest = _read(bootstrap.manifest_path(day))
    origin = manifest.get('selected_release_sha')
    if not origin or origin != _preopen(day).get('selected_release_commit'):
        raise ValueError('entry_consumer_origin_invalid')
    bound = manifest.get('pre_submit_delay_handoff') or {}
    if bound.get('status') != 'verified_initial_timing_policy':
        return dict(status='not_applicable', target_date=day)
    if bound.get('target_date') != day or not bound.get('code_contract_sha256'):
        raise ValueError('entry_consumer_policy_binding_invalid')
    from src.engine.scalping.pre_submit_delay_initial_policy import CONTRACT_PATHS
    changed = _verify_entry_code_delta(root, commit, origin,
        {name: name for name in CONTRACT_PATHS}, bound['code_contract_sha256'])
    return dict(status='pass', target_date=day, origin_commit=origin,
                release_commit=commit, changed_consumer_paths=changed,
                policy_effect='unchanged', actual_pid_consumed=False)


def verify_candidate_stop_code(day, root, commit):
    """Pre-stop source-exact stop-code check; never select/rewrite a policy."""
    _today(day, None)
    root = Path(root).resolve(strict=True)
    if Path(__file__).resolve().parents[3] != root:
        raise ValueError('entry_consumer_candidate_code_mismatch')
    manifest = _read(bootstrap.manifest_path(day))
    origin = manifest.get('selected_release_sha')
    if not origin or origin != _preopen(day).get('selected_release_commit'):
        raise ValueError('entry_consumer_origin_invalid')
    from src.engine.scalping import main_stop_policy as S
    env = manifest.get('env_overrides') or {}
    if not env.get(S.ENV_FILE):
        return dict(status='pass', applicability='not_installed', target_date=day)
    bundle = S.load_bundle(env[S.ENV_FILE], env[S.ENV_SHA], day, require_current_code=False)
    bound = manifest.get('main_stop_confirmation_receipt') or {}
    if bound.get('policy_sha256') != bundle['policy_sha256'] or bound.get('target_date') != day:
        raise ValueError('entry_consumer_policy_binding_invalid')
    if bundle['code_sha256'] == S.implementation_sha():
        changed = []
    else:
        if any(c['status'] == 'selected' for c in bundle['cells'].values()):
            raise ValueError('stop_bundle_code_generation_changed')
        changed = _verify_entry_code_delta(root, commit, origin,
            {name:'src/engine/'+name for name in S.implementation_paths()}, bundle['code_sha256'])
    return dict(status='pass', target_date=day, origin_commit=origin, release_commit=commit,
                changed_consumer_paths=changed, policy_effect='unchanged', actual_pid_consumed=False)


def verify_candidate_holding_vote_code(day, root, commit):
    """Check the original holding-vote code pin before changing selection.

    Only incumbent carry can cross a reviewed code delta. Full source handoff
    and the unchanged policy receipt remain mandatory during preparation.
    """
    _today(day, None)
    root = Path(root).resolve(strict=True)
    if Path(__file__).resolve().parents[3] != root:
        raise ValueError('entry_consumer_candidate_code_mismatch')
    manifest = _read(bootstrap.manifest_path(day))
    origin = manifest.get('selected_release_sha')
    if not origin or origin != _preopen(day).get('selected_release_commit'):
        raise ValueError('entry_consumer_origin_invalid')
    bound = manifest.get('holding_path_vote_policy_receipt') or {}
    from src.engine.scalping import holding_path_vote_policy as V
    from src.engine.scalping.holding_vote_experiment import code_sha, _code_paths
    if not bound.get('allowed_runtime_apply'):
        if bound.get('status') != 'baseline_policy_not_published' or V.policy_path(DATA_DIR, day).exists():
            raise ValueError('holding_vote_candidate_policy_not_verified')
        return dict(status='pass', applicability='not_installed', target_date=day)
    bundle = V.load_bundle(DATA_DIR, day, require_current_code=False)
    if (bound.get('bundle_sha256') != bundle.get('bundle_sha256')
            or bound.get('target_date') != day
            or bound.get('path') != str(V.policy_path(DATA_DIR, day))):
        raise ValueError('entry_consumer_policy_binding_invalid')
    changed = []
    if bundle.get('schema') == V.SUCCESSOR_SCHEMA and bundle.get('code_sha256') != code_sha():
        if bundle.get('selection_mode') != 'incumbent_carry':
            raise ValueError('holding_vote_successor_code_changed')
        changed = _verify_entry_code_delta(root, commit, origin,
            {name: 'src/engine/' + name for name in _code_paths()}, bundle['code_sha256'])
    return dict(status='pass', target_date=day, origin_commit=origin, release_commit=commit,
                changed_consumer_paths=changed, policy_effect='unchanged', actual_pid_consumed=False)


def _checked_bootstrap(day, pid):
    options = {'observer_reuse': True} if _OBSERVER_CUSTODY.get() is not None else {}
    check = bootstrap.verify_bootstrap(day, pid=pid, write=False, **options)
    if check.get("status") != "pass":
        raise ValueError("intraday_bootstrap_invalid:" + ",".join(check.get("findings") or []))
    from src.engine.automation.auxiliary_reader_readiness import verify_auxiliary_reader
    verify_auxiliary_reader(day, data_root=DATA_DIR)
    return check


def prepare(day, *, old_pid, previous_root, confirm, now=None, reseal_postclose_source=False,
            previous_stopped=False, freeze_operating_checklist=False):
    token = _STOPPED_PREPARATION.set(
        (day, int(old_pid), str(Path(previous_root).resolve())) if previous_stopped else None)
    native_token = _NATIVE_PREDECESSOR.set(None)
    try:
        return _prepare(day, old_pid=old_pid, previous_root=previous_root, confirm=confirm,
                        now=now, reseal_postclose_source=reseal_postclose_source,
                        previous_stopped=previous_stopped, freeze_operating_checklist=freeze_operating_checklist)
    finally:
        _NATIVE_PREDECESSOR.reset(native_token)
        _STOPPED_PREPARATION.reset(token)


def _prepare(day, *, old_pid, previous_root, confirm, now=None, reseal_postclose_source=False,
             previous_stopped=False, freeze_operating_checklist=False):
    current = _today(day, now)
    if confirm != CONFIRM:
        raise ValueError("intraday_handoff_explicit_authority_required")
    root, commit = _selection()
    previous = Path(previous_root).resolve(strict=True)
    managed = (DATA_DIR.parent.parent / f"{DATA_DIR.parent.name}-runtime-releases").resolve()
    if previous.parent != managed or previous == root:
        raise ValueError("intraday_previous_release_invalid")
    old_commit = subprocess.check_output(["git", "-C", str(previous), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(previous), "status", "--porcelain", "--", "src", "deploy", "restart.sh"], text=True).strip()
    original = _preopen(day)
    if previous_stopped and original.get('selected_release_commit') == old_commit:
        selection = _read(DATA_DIR / 'runtime/runtime_release_selection.json')
        if (selection.get('approved_by') != 'user'
                or selection.get('approval_scope') != 'ordered_intraday_deploy_and_restart'
                or selection.get('previous_release_root') != str(Path(previous_root).resolve())
                or Path('/proc', str(int(old_pid))).exists()):
            raise ValueError('intraday_native_predecessor_not_stopped')
        path = selection.get('native_predecessor_path')
        identity = (_read(path).get('verification') or {}).get('pid_identity') or {}
        if identity.get('pid') != int(old_pid):
            raise ValueError('intraday_native_predecessor_pid_invalid')
        native = _native_predecessor(day, selection['git_commit'], previous_root,
            selection['previous_git_commit'], identity, path, selection.get('native_predecessor_sha256'))
        _NATIVE_PREDECESSOR.set(native)
    native_predecessor = _NATIVE_PREDECESSOR.get()
    if previous_stopped:
        # Explicit recovery of an attested but terminated predecessor. Never
        # fabricate live PID consumption from a historical bootstrap receipt.
        if Path('/proc', str(int(old_pid))).exists():
            raise ValueError('intraday_previous_pid_still_exists')
        previous_consumed_path = (Path(native_predecessor['path']) if native_predecessor
                                  else _paths(day, old_commit)[1])
        previous_consumed_sha = _sha(previous_consumed_path)
        old_identity = (native_predecessor['identity'] if native_predecessor
                        else _read(previous_consumed_path).get('pid_identity') or {})
        if old_identity.get('pid') != int(old_pid) or not old_identity.get('start_ticks'):
            raise ValueError('intraday_stopped_identity_unattested')
        if original.get('selected_release_commit') == old_commit and not native_predecessor:
            raise ValueError('intraday_stopped_consumed_handoff_required')
    else:
        old_identity = _identity(old_pid)
    # A subsequent same-day handoff may use the preceding verified consumption.
    if original.get("selected_release_commit") != old_commit:
        prior_path, prior_consumed = _paths(day, old_commit)
        prior = _read(prior_path)
        consumed = _read(prior_consumed)
        if (prior.get('schema') != 'intraday_policy_preserving_release_handoff_v1'
                or prior.get('status') != 'prepared_verified'
                or prior.get('authority') != CONFIRM or prior.get('target_date') != day
                or prior.get('selected_release_commit') != old_commit
                or prior.get('release_root') != str(previous)
                or _sha(_preopen_path(day)) != prior.get("preopen_sha256")
                or consumed.get('schema') != 'intraday_policy_preserving_consumption_v1'
                or consumed.get('status') != 'pass' or consumed.get('target_date') != day
                or consumed.get('selected_release_commit') != old_commit
                or consumed.get('release_root') != str(previous)
                or consumed.get('actual_pid_consumed') is not True
                or consumed.get('pid_identity') != old_identity
                or consumed.get("handoff_sha256") != _sha(prior_path)):
            raise ValueError("intraday_previous_consumption_invalid")
    if dirty or old_identity["cwd"] != str(previous / "src"):
        raise ValueError("intraday_previous_pid_or_release_invalid")
    check = _checked_bootstrap(day, None if previous_stopped else old_pid)
    prepared_index = DATA_DIR / "runtime/policy_bootstrap/prepared" / day / "latest.json"
    prepared = _read(prepared_index)
    receipt_path = Path(prepared["receipt_path"])
    prepared_root = prepared_index.parent.resolve()
    if (receipt_path.resolve().parent.parent != prepared_root
            or _sha(receipt_path) != prepared.get("receipt_sha256")):
        raise ValueError("intraday_original_prepared_invalid")
    frozen = [bootstrap.env_path(day), bootstrap.manifest_path(day), _preopen_path(day), prepared_index, receipt_path]
    if native_predecessor:
        frozen.append(previous_consumed_path)
    if original.get('selected_release_commit') != old_commit:
        if (consumed.get('manifest_sha256') != check.get('manifest_sha256')
                or prior.get('prepared_receipt_path') != str(receipt_path)
                or prior.get('prepared_receipt_sha256') != _sha(receipt_path)
                or any(prior.get('frozen_files', {}).get(str(path)) != _sha(path) for path in frozen)):
            raise ValueError('intraday_previous_generation_changed')
    reseal = None
    if reseal_postclose_source:
        from src.engine.automation.next_preopen_readiness import _source_receipts
        original_prepared = _read(receipt_path)
        source_day = original_prepared.get('source_date')
        if (original_prepared.get('schema') != 'next_preopen_readiness_v1'
                or original_prepared.get('status') != 'prepared_verified'
                or original_prepared.get('target_date') != day
                or original_prepared.get('actual_pid_consumed') is not False):
            raise ValueError('intraday_original_prepared_contract_invalid')
        # Reuse the exact sealed whole-chain PASS and independently checked
        # live old PID. Re-evaluating the new selector here would require its
        # own consumed receipt before prepare/launch, a circular second-handoff
        # gate. Every source hash and dated policy byte must still match; the
        # launcher/consumers recheck the full contract after the new PID binds.
        controller = _read(DATA_DIR/'report/postclose_done_controller'/f'postclose_done_controller_{source_day}.json')
        strict = _read(controller['verification_attempt_path']) if controller.get('verification_attempt_path') else {}
        old_checklist = (strict.get('checklist_handoff') or {}).get('path')
        expected = (strict.get('generation_binding') or {}).get('checklist_sha256')
        historical = None
        try:
            old_checklist_sha = _sha(old_checklist) if old_checklist else None
        except FileNotFoundError:
            # A removed executable release can have owned the original docs
            # symlink. Absence permits only the same exact-hash Git/preserved
            # snapshot path below, never a fresh document or relaxed binding.
            old_checklist_sha = None
        if old_checklist and old_checklist_sha != expected:
            relative = 'docs/checklists/' + day + '-stage2-todo-checklist.md'
            origin_commit, predecessor = old_commit, None
            if original.get('selected_release_commit') != old_commit:
                inherited = (prior.get('postclose_source_reseal') or {}).get('historical_checklist')
                if inherited:
                    historical_prior, predecessor = _historical_predecessor(day, old_commit, expected)
                    origin_commit = historical_prior['git_commit']
            try:
                original_bytes = subprocess.check_output(
                    ['git', '-C', str(previous), 'show', origin_commit + ':' + relative],
                    stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                # A PREOPEN-generated document may not exist in the earlier
                # release tree. Only the exact strict-bound snapshot below can
                # replace missing Git bytes; current edited docs cannot.
                original_bytes = b''
            original_basis='original_whole_chain_checklist_generation'
            if hashlib.sha256(original_bytes).hexdigest() != expected:
                # Native postclose writes the checklist after the release was
                # committed. Its strict-bound bytes need not be a Git blob.
                preserved=DATA_DIR/'runtime/policy_bootstrap/historical_checklists'/(expected+'.md')
                if not preserved.exists() or _sha(preserved)!=expected:
                    raise ValueError('intraday_original_checklist_git_generation_missing')
                original_bytes=preserved.read_bytes()
                original_basis='strict_bound_postclose_generated_checklist'
            snapshot = _paths(day, commit)[0].parent / (commit + '.historical-checklist.md')
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            if snapshot.exists():
                if snapshot.read_bytes() != original_bytes:
                    raise ValueError('intraday_historical_checklist_snapshot_changed')
            else:
                with snapshot.open('xb') as out:
                    out.write(original_bytes); out.flush(); os.fsync(out.fileno())
            historical = dict(path=str(snapshot), sha256=expected, git_commit=origin_commit,
                              git_path=relative, basis=original_basis)
            if predecessor:
                historical['predecessor'] = predecessor
            frozen.append(snapshot)
        source = _source_receipts(source_day, day, generation_only=True,
                                 **({'checklist_snapshot': Path(historical['path'])} if historical else {}))
        if not source.get('policy_receipts') or source['policy_receipts'] != original_prepared.get('policy_receipts'):
            raise ValueError('intraday_reseal_policy_generation_changed')
        checklist = DATA_DIR.parent / 'docs/checklists' / (day + '-stage2-todo-checklist.md')
        operating = _freeze_operating_checklist(day, commit, checklist) if freeze_operating_checklist else None
        frozen.extend([Path(source['controller_path']), Path(source['summary_path']),
                       Path(operating['path']) if operating else checklist])
        reseal = dict(source_date=source_day, target_date=day, current_source_receipts=source,
                      checklist_path=str(checklist), original_controller_sha256=original_prepared.get('controller_sha256'),
                      original_summary_sha256=original_prepared.get('summary_sha256'), policy_effect='unchanged')
        if historical: reseal['historical_checklist'] = historical
        if operating: reseal['operating_checklist'] = operating
    # All native source receipts remain independently validated by the launcher.
    hashes = {str(path): _sha(path) for path in frozen}
    if reseal is not None and any(hashes[source[key + '_path']] != source[key + '_sha256']
                                  for key in ('controller', 'summary')):
        raise ValueError('intraday_postclose_generation_changed_during_prepare')
    if previous_stopped:
        if (Path('/proc', str(int(old_pid))).exists()
                or _sha(previous_consumed_path) != previous_consumed_sha):
            raise ValueError('intraday_stopped_predecessor_changed')
    elif _identity(old_pid) != old_identity:
        raise ValueError("intraday_old_pid_changed_during_prepare")
    payload = {"schema": "intraday_policy_preserving_release_handoff_v1", "status": "prepared_verified",
               "target_date": day, "selected_release_commit": commit, "release_root": str(root),
               "previous_release_root": str(previous), "previous_release_commit": old_commit,
               "old_pid_identity": old_identity, "prepared_at": current.isoformat(),
               "first_launch_before": (current + timedelta(minutes=15)).isoformat(),
               "preopen_sha256": hashes[str(_preopen_path(day))], "frozen_files": hashes,
               "prepared_receipt_path": str(receipt_path), "prepared_receipt_sha256": _sha(receipt_path),
               "manifest_sha256": check.get("manifest_sha256"), "actual_pid_consumed": False,
               "policy_effect": "unchanged", "authority": confirm}
    if reseal is not None:
        payload['postclose_source_reseal'] = reseal
    if previous_stopped:
        payload['previous_process_state'] = ('stopped_native_preopen_consumption_verified'
            if native_predecessor else 'stopped_historical_consumption_verified')
        payload['previous_consumption_sha256'] = previous_consumed_sha
        if native_predecessor:
            payload['native_predecessor_path'] = str(previous_consumed_path)
    path, _ = _paths(day, commit)
    path.parent.mkdir(parents=True, exist_ok=True)
    # A receipt is immutable. Repeating preparation cannot silently replace it.
    content = json.dumps(payload, sort_keys=True, indent=2) + "\n"
    with path.open("x", encoding="utf-8") as output:
        output.write(content)
        output.flush()
        os.fsync(output.fileno())
    return verify(day, commit, now=current)


def verify(day, commit, *, now=None):
    return _verify_handoff(day, commit, now=now)


def _freeze_operating_checklist(day, commit, checklist):
    import stat
    with os.fdopen(os.open(checklist, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > 2*1024*1024:
            raise ValueError('intraday_operating_checklist_invalid')
        content = stream.read(2*1024*1024+1)
        after = checklist.lstat()
        identity = lambda s: (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
        if len(content) != before.st_size or identity(before) != identity(after):
            raise ValueError('intraday_operating_checklist_changed_during_read')
    path = _paths(day, commit)[0].parent/(commit+'.operating-checklist.md')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(content); stream.flush(); os.fsync(stream.fileno())
    return dict(path=str(path), sha256=hashlib.sha256(content).hexdigest(),
                source_path=str(checklist), target_date=day, role='launch_document_snapshot')


def _verify_handoff(day, commit, *, now=None, historical_observer=False):
    """Keep launch verification strict; historical observation uses sealed sources."""
    findings = []
    payload = {}
    try:
        current = _today(day, now)
        # Read-only consumers may run from their own reviewed immutable
        # report release. Prepare/consume keep the selected-root requirement.
        root, selected = _selection(require_selected_cwd=False)
        path, consumed_path = _paths(day, commit)
        payload = _read(path)
        if (selected != commit or payload.get("schema") != "intraday_policy_preserving_release_handoff_v1"
                or payload.get("status") != "prepared_verified" or payload.get("authority") != CONFIRM
                or payload.get("target_date") != day or payload.get("selected_release_commit") != commit
                or payload.get("release_root") != str(root) or payload.get("actual_pid_consumed") is not False):
            raise ValueError("intraday_handoff_identity_invalid")
        _preopen(day)
        native_predecessor = None
        if payload.get('previous_process_state'):
            if payload['previous_process_state'] == 'stopped_native_preopen_consumption_verified':
                native_predecessor = _native_predecessor(day, commit,
                    payload['previous_release_root'], payload['previous_release_commit'],
                    payload['old_pid_identity'], payload.get('native_predecessor_path'),
                    payload.get('previous_consumption_sha256'))
            else:
                predecessor = _paths(day, payload['previous_release_commit'])[1]
                if (payload['previous_process_state'] != 'stopped_historical_consumption_verified'
                    or _sha(predecessor) != payload.get('previous_consumption_sha256')
                    or _read(predecessor).get('pid_identity') != payload.get('old_pid_identity')):
                    raise ValueError('intraday_stopped_predecessor_changed')
        frozen = payload["frozen_files"]
        required = {str(bootstrap.env_path(day)), str(bootstrap.manifest_path(day)), str(_preopen_path(day)),
                    str(DATA_DIR / "runtime/policy_bootstrap/prepared" / day / "latest.json"),
                    payload["prepared_receipt_path"]}
        if native_predecessor:
            required.add(native_predecessor['path'])
        reseal = payload.get('postclose_source_reseal')
        if reseal is not None:
            prepared_receipt = _read(payload['prepared_receipt_path'])
            source = reseal['current_source_receipts']
            if (reseal.get('target_date') != day or reseal.get('source_date') != prepared_receipt.get('source_date')
                    or reseal.get('policy_effect') != 'unchanged'
                    or source.get('policy_receipts') != prepared_receipt.get('policy_receipts')
                    or reseal.get('checklist_path') != str(DATA_DIR.parent / 'docs/checklists' / (day + '-stage2-todo-checklist.md'))
                    or source.get('controller_path') != str(DATA_DIR / 'report/postclose_done_controller' / ('postclose_done_controller_' + reseal['source_date'] + '.json'))
                    or source.get('summary_path') != str(DATA_DIR / 'report/runtime_approval_summary' / ('runtime_approval_summary_' + reseal['source_date'] + '.json'))):
                raise ValueError('intraday_postclose_reseal_identity_invalid')
            if any(frozen.get(source[key + '_path']) != source.get(key + '_sha256')
                   for key in ('controller', 'summary')):
                raise ValueError('intraday_postclose_reseal_hash_invalid')
            snapshot = reseal.get('historical_checklist')
            if snapshot:
                expected_path = _paths(day, commit)[0].parent / (commit + '.historical-checklist.md')
                strict = _read(_read(source['controller_path'])['verification_attempt_path'])
                origin_commit = payload['previous_release_commit']
                if snapshot.get('predecessor'):
                    inherited, predecessor = _historical_predecessor(day, origin_commit, snapshot['sha256'])
                    if predecessor != snapshot['predecessor']:
                        raise ValueError('intraday_historical_predecessor_changed')
                    origin_commit = inherited['git_commit']
                if (snapshot.get('path') != str(expected_path)
                        or snapshot.get('sha256') != strict['generation_binding']['checklist_sha256']
                        or frozen.get(str(expected_path)) != snapshot['sha256']
                        or snapshot.get('git_commit') != origin_commit
                        or snapshot.get('git_path') != 'docs/checklists/' + day + '-stage2-todo-checklist.md'):
                    raise ValueError('intraday_historical_checklist_binding_invalid')
                required.add(str(expected_path))
            operating = reseal.get('operating_checklist')
            if operating is not None:
                operating_path = path.parent/(commit+'.operating-checklist.md')
                if (operating.get('path') != str(operating_path) or operating_path.is_symlink()
                        or operating.get('source_path') != reseal['checklist_path']
                        or operating.get('target_date') != day or operating.get('role') != 'launch_document_snapshot'
                        or frozen.get(str(operating_path)) != operating.get('sha256')):
                    raise ValueError('intraday_operating_checklist_binding_invalid')
                required.add(str(operating_path))
            else:
                required.add(reseal['checklist_path'])
            required.update([source['controller_path'], source['summary_path']])
        historical_document = None
        if historical_observer:
            # Only an already-consumed historical handoff may disregard edits
            # to the operational checklist. Its sealed snapshot and all other
            # sources remain required. Public verify/consume/activation never
            # take this branch, and the observer binds the live PID separately.
            if not reseal or not reseal.get('historical_checklist') or not consumed_path.exists():
                raise ValueError('intraday_observer_consumed_historical_handoff_required')
            historical_document = reseal['checklist_path'] if not reseal.get('operating_checklist') else None
        if set(frozen) != required or any(_sha(name) != sha for name, sha in frozen.items()
                                         if name != historical_document):
            raise ValueError("intraday_preserved_generation_changed")
        start = datetime.fromisoformat(payload["prepared_at"])
        deadline = datetime.fromisoformat(payload["first_launch_before"])
        if (start.tzinfo is None or deadline.tzinfo is None or start > current
                or deadline != start + timedelta(minutes=15)):
            raise ValueError("intraday_handoff_clock_invalid")
        consumed = None
        if consumed_path.exists():
            consumed = _read(consumed_path)
            if (consumed.get("handoff_sha256") != _sha(path) or consumed.get("target_date") != day
                    or consumed.get("selected_release_commit") != commit
                    or consumed.get("actual_pid_consumed") is not True
                    or consumed.get("release_root") != str(root)):
                raise ValueError("intraday_consumption_invalid")
        elif current > deadline:
            raise ValueError("intraday_first_launch_window_expired")
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        findings.append(str(exc))
    return {"status": "pass" if not findings else "fail", "target_date": day,
            "findings": findings, "basis": "intraday_policy_preserving_handoff",
            "handoff": payload, "actual_pid_consumed": False}


def verify_pid_consumption(day, *, pid, now=None):
    """Read-only proof of the selected release's exact live child consumption."""
    try:
        current = _today(day, now)
        root, commit = _selection(require_selected_cwd=False)
        identity = _identity(pid)
        if identity['cwd'] != str(root / 'src'):
            raise ValueError('intraday_consumption_pid_root_invalid')
        path, consumed_path = _paths(day, commit)
        frozen = {_preopen_path(day): _sha(_preopen_path(day)),
                  bootstrap.env_path(day): _sha(bootstrap.env_path(day)),
                  bootstrap.manifest_path(day): _sha(bootstrap.manifest_path(day))}
        native = not path.exists()
        if native:
            if _preopen(day).get('selected_release_commit') != commit:
                raise ValueError('intraday_consumption_handoff_missing')
        else:
            frozen.update({path: _sha(path), consumed_path: _sha(consumed_path)})
            check = _verify_consumed_handoff(day, commit, now=current)
            if check['status'] != 'pass':
                return check
            consumed = _read(consumed_path)
            if (consumed.get('schema') != 'intraday_policy_preserving_consumption_v1'
                    or consumed.get('status') != 'pass'
                    or consumed.get('actual_pid_consumed') is not True
                    or consumed.get('target_date') != day
                    or consumed.get('selected_release_commit') != commit
                    or consumed.get('release_root') != str(root)
                    or consumed.get('handoff_sha256') != frozen[path]
                    or consumed.get('pid_identity') != identity):
                raise ValueError('intraday_consumption_current_pid_not_bound')
        checked = _checked_bootstrap(day, pid)
        manifest_sha = checked.get('manifest_sha256')
        if not manifest_sha or (not native and consumed.get('manifest_sha256') != manifest_sha):
            raise ValueError('intraday_consumption_manifest_mismatch')
        if (any(_sha(p) != sha for p, sha in frozen.items())
                or (native and path.exists())
                or _identity(pid) != identity
                or _selection(require_selected_cwd=False) != (root, commit)):
            raise ValueError('intraday_consumption_generation_changed')
        return dict(schema='intraday_pid_consumption_verification_v1', status='pass', findings=[],
                    target_date=day, selected_release_commit=commit, release_root=str(root),
                    basis='native_preopen' if native else 'intraday_policy_preserving_handoff',
                    pid_identity=identity, actual_pid_consumed=True, manifest_sha256=manifest_sha)
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        return dict(status='fail', findings=[str(exc)], target_date=day, actual_pid_consumed=False)


def _verify_consumed_handoff(day, commit, *, now=None):
    """Existing live policy custody; never a launch/consume/activation gate."""
    try:
        root, selected = _selection(require_selected_cwd=False)
        path, consumed_path = _paths(day, commit)
        handoff_sha, consumed_sha = _sha(path), _sha(consumed_path)
        consumed = _read(consumed_path)
        identity = consumed.get('pid_identity') or {}
        if (selected != commit or consumed.get('schema') != 'intraday_policy_preserving_consumption_v1'
                or consumed.get('status') != 'pass' or consumed.get('actual_pid_consumed') is not True
                or consumed.get('target_date') != day or consumed.get('selected_release_commit') != commit
                or consumed.get('release_root') != str(root) or consumed.get('handoff_sha256') != handoff_sha
                or identity.get('cwd') != str(root/'src') or _identity(identity['pid']) != identity):
            raise ValueError('intraday_consumed_live_identity_invalid')
        historical = bool((_read(path).get('postclose_source_reseal') or {}).get('historical_checklist'))
        result = _verify_handoff(day, commit, now=now, historical_observer=historical)
        if consumed.get('manifest_sha256') != result.get('handoff', {}).get('manifest_sha256'):
            raise ValueError('intraday_consumed_manifest_changed')
        if (_sha(path) != handoff_sha or _sha(consumed_path) != consumed_sha
                or _identity(identity['pid']) != identity
                or _selection(require_selected_cwd=False) != (root, commit)):
            raise ValueError('intraday_consumed_generation_changed')
        return result
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return dict(status='fail', findings=[str(exc)], target_date=day, actual_pid_consumed=False)


def verify_predecessor_consumption(day, *, pid):
    """Candidate's full read-only revalidation before an ordered cutover.

    The candidate must be immutable, and every affected policy consumer must
    pass its exact reviewed source-pair gate. This does not attest candidate
    consumption or change the selector, checklist, policy or predecessor.
    """
    from src.engine.infrastructure import runtime_release_router as router
    root, commit = _selection(require_selected_cwd=False)
    candidate = Path(__file__).resolve().parents[3]
    candidate_commit = router.git(candidate, 'rev-parse', 'HEAD')
    router.validate_release(DATA_DIR.parent, dict(schema='runtime_release_selection_v1',
        workspace=str(DATA_DIR.parent), release_root=str(candidate), git_commit=candidate_commit))
    if root == candidate:
        raise ValueError('intraday_predecessor_candidate_already_selected')
    identity = _identity(pid)
    token = _PREDECESSOR_REVIEW.set(dict(day=day, root=root, commit=commit,
        code_root=candidate, code_commit=candidate_commit, identity=identity))
    try:
        result = verify_pid_consumption(day, pid=pid)
        if result.get('status') == 'pass':
            result.update(verification_code_root=str(candidate), verification_code_commit=candidate_commit,
                          candidate_pid_consumed=False, runtime_effect=False)
        return result
    finally:
        _PREDECESSOR_REVIEW.reset(token)


def consume(day, *, pid, now=None):
    _, commit = _selection()
    path, consumed_path = _paths(day, commit)
    if not path.exists():
        return {"status": "pass", "basis": "native_preopen", "actual_pid_consumed": False}
    check = verify(day, commit, now=now)
    if check["status"] != "pass":
        return check
    identity = _identity(pid)
    if identity["cwd"] != str(Path(check["handoff"]["release_root"]) / "src"):
        raise ValueError("intraday_new_pid_root_invalid")
    verified = _checked_bootstrap(day, pid)
    if _identity(pid) != identity:
        raise ValueError("intraday_new_pid_changed_during_verify")
    payload = {"schema": "intraday_policy_preserving_consumption_v1", "status": "pass", "target_date": day,
               "selected_release_commit": commit, "release_root": check["handoff"]["release_root"],
               "handoff_sha256": _sha(path), "pid_identity": identity, "actual_pid_consumed": True,
               "manifest_sha256": verified.get("manifest_sha256"),
               "verified_at": (now or datetime.now(KST)).isoformat()}
    bootstrap._publish(consumed_path, json.dumps(payload, sort_keys=True, indent=2) + "\n")
    return payload


def historical_checklist_for_observer(project, source_date, *, now=None):
    """Resolve a consumed, same-day handoff for historical generation observers.

    This receipt cannot publish a new finalization or whole-chain completion.
    The caller must still check every other source and the original DONE hashes.
    """
    try:
        return _historical_checklist_for_observer(project, source_date, now=now)
    except (OSError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        raise ValueError('intraday_observer_receipt_unavailable:' + type(exc).__name__) from exc


def _historical_checklist_for_observer(project, source_date, *, now=None):
    current = now or datetime.now(KST)
    day = current.astimezone(KST).date().isoformat()
    if (Path(project) / 'data').resolve() != DATA_DIR.resolve():
        raise ValueError('intraday_observer_data_root_mismatch')
    root, commit = _selection(require_selected_cwd=False)
    handoff_path, consumed_path = _paths(day, commit)
    handoff_sha = _sha(handoff_path)
    check = _verify_handoff(day, commit, now=current, historical_observer=True)
    if check['status'] != 'pass':
        raise ValueError('intraday_observer_handoff_invalid:' + ','.join(check['findings']))
    preserved = check['handoff']
    reseal = preserved.get('postclose_source_reseal') or {}
    historical = reseal.get('historical_checklist') or {}
    if (reseal.get('source_date') != source_date or reseal.get('target_date') != day
            or not historical or reseal.get('policy_effect') != 'unchanged'):
        raise ValueError('intraday_observer_source_scope_mismatch')
    consumed_sha = _sha(consumed_path)
    consumed = _read(consumed_path)
    identity = consumed.get('pid_identity') or {}
    if (consumed.get('schema') != 'intraday_policy_preserving_consumption_v1'
            or consumed.get('status') != 'pass' or consumed.get('actual_pid_consumed') is not True
            or consumed.get('handoff_sha256') != handoff_sha
            or consumed.get('target_date') != day or consumed.get('selected_release_commit') != commit
            or consumed.get('release_root') != str(root)
            or identity.get('cwd') != str(root / 'src')
            or _identity(identity['pid']) != identity):
        raise ValueError('intraday_observer_current_pid_not_bound')
    token = _OBSERVER_CUSTODY.set((day, commit))
    try:
        bootstrap_check = _checked_bootstrap(day, identity['pid'])
    finally:
        _OBSERVER_CUSTODY.reset(token)
    if (consumed.get('manifest_sha256') != bootstrap_check.get('manifest_sha256')
            or _identity(identity['pid']) != identity
            or _sha(handoff_path) != handoff_sha
            or _sha(consumed_path) != consumed_sha
            or _selection(require_selected_cwd=False) != (root, commit)):
        raise ValueError('intraday_observer_pid_generation_changed')
    return dict(schema='intraday_historical_checklist_observer_v1',
        basis='consumed_intraday_preserved_historical_generation',
        source_date=source_date, target_date=day, release_commit=commit,
        path=historical['path'], sha256=historical['sha256'],
        handoff_path=str(handoff_path), handoff_sha256=handoff_sha,
        consumed_path=str(consumed_path), consumed_sha256=consumed_sha,
        delay_observer_validation=bootstrap_check.get('delay_observer_validation'),
        pid_identity=identity, runtime_effect=False, new_finalization_claimed=False)


def activate_main_v2(day,*,pid,confirm,now=None):
    """Apply an approved Main policy only after the reviewed code PID binds."""
    current=_today(day,now)
    if confirm!='APPROVED_INTRADAY_MAIN_POLICY_ACTIVATION':
        raise ValueError('intraday_main_policy_explicit_authority_required')
    root,commit=_selection();identity=_identity(pid)
    if identity['cwd']!=str(root/'src'):raise ValueError('intraday_main_policy_pid_release_mismatch')
    check=verify(day,commit,now=current)
    _,consumed_path=_paths(day,commit);consumed=_read(consumed_path)
    if (check['status']!='pass' or consumed.get('status')!='pass'
            or consumed.get('pid_identity')!=identity or consumed.get('actual_pid_consumed') is not True
            or consumed.get('selected_release_commit')!=commit):
        raise ValueError('intraday_main_policy_code_consumption_missing')
    verified=_checked_bootstrap(day,pid)
    evidence={'schema':'intraday_main_policy_code_pid_v1','target_date':day,'release_commit':commit,
              'pid_identity':identity,'consumed_path':str(consumed_path),'consumed_sha256':_sha(consumed_path),
              'manifest_sha256':verified['manifest_sha256'],'verified_at':current.isoformat(),
              'custody_and_order_paths':'existing_native_main_guards_unchanged'}
    if _identity(pid)!=identity:raise ValueError('intraday_main_policy_pid_changed')
    from src.engine.scalping.continuous_reversal_policy_v2 import activate
    candidate = DATA_DIR/'runtime/mechanistic_entry_policy/candidates'/f'policy_{day}.json'
    if candidate.is_file() and json.loads(candidate.read_text())['continuous_reversal']['schema'] in {'continuous_reversal_policy_v5','continuous_reversal_policy_v6'}:
        # v5 is issued as next_session and consumed by the PREOPEN path. Do not
        # reinterpret it with the older intraday activation contract.
        raise ValueError('operating_v5_requires_next_session_activation')
    if candidate.is_file() and json.loads(candidate.read_text())['continuous_reversal']['schema']=='continuous_reversal_policy_v3':
        from src.engine.scalping.continuous_reversal_policy_v3 import activate
    if candidate.is_file() and json.loads(candidate.read_text())['continuous_reversal']['schema']=='continuous_reversal_policy_v4':
        from src.engine.scalping.continuous_reversal_policy_v4 import activate
    receipt=activate(DATA_DIR,day,now=current,intraday_evidence=evidence)
    return dict(status='pass',activation=receipt,actual_policy_pid_consumption=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--verify", action="store_true")
    group.add_argument("--verify-predecessor", action="store_true")
    group.add_argument("--consume", action="store_true")
    group.add_argument('--activate-main-v2',action='store_true')
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--old-pid", type=int)
    parser.add_argument("--validation-session", help="internal transition digest scope; no verdict reuse")
    parser.add_argument("--pid", type=int)
    parser.add_argument("--previous-root")
    parser.add_argument("--confirm")
    parser.add_argument('--reseal-postclose-source', action='store_true')
    parser.add_argument('--previous-stopped', action='store_true')
    parser.add_argument('--freeze-operating-checklist', action='store_true')
    args = parser.parse_args(argv)
    if args.validation_session and args.activate_main_v2:
        parser.error("validation session cannot wrap policy activation")
    from src.engine.infrastructure.validation_digest_session import transition_session, ValidationDeferred
    session = None
    try:
        with transition_session(DATA_DIR, args.target_date, args.validation_session, args.pid) as session:
            if args.prepare:
                result = prepare(args.target_date, old_pid=args.old_pid, previous_root=args.previous_root,
                                 confirm=args.confirm, reseal_postclose_source=args.reseal_postclose_source,
                                 previous_stopped=args.previous_stopped,
                                 freeze_operating_checklist=args.freeze_operating_checklist)
            elif args.activate_main_v2:
                result=activate_main_v2(args.target_date,pid=args.pid,confirm=args.confirm)
            elif args.consume:
                result = consume(args.target_date, pid=args.pid)
            elif args.verify_predecessor:
                result = verify_predecessor_consumption(args.target_date, pid=args.pid)
            elif args.pid is not None:
                result = verify_pid_consumption(args.target_date, pid=args.pid)
            else:
                result = verify(args.target_date, _selection(require_selected_cwd=False)[1])
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError, ValidationDeferred) as exc:
        result = {"status": "fail", "findings": [str(exc)]}
    if session is not None:
        result['validation_io'] = session.stats
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    # Nested policy readers import the canonical module. Running prepare on a
    # second __main__ copy would give them different ContextVar instances.
    from src.engine.automation.intraday_release_handoff import main as canonical_main
    raise SystemExit(canonical_main())
