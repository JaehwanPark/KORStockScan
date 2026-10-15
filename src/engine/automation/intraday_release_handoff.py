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
    _today(day, None)
    root, commit = _selection(require_selected_cwd=False)
    if Path(__file__).resolve().parents[3] != root:
        raise ValueError('entry_consumer_release_mismatch')
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
    current_path, _ = _paths(day, commit)
    if current_path.exists():
        # Only the read-only historical observer's nested policy validation may
        # use the already-consumed sealed document. Public startup stays strict.
        checked = (_verify_handoff(day, commit, historical_observer=True)
                   if _OBSERVER_CUSTODY.get() == (day, commit) else verify(day, commit))
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
    changed = _verify_entry_code_delta(root, commit, origin, paths, expected)
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
    for key, name in paths.items():
        before = revision_bytes(origin, name)
        after = (root / name).read_bytes()
        if after != revision_bytes(commit, name):
            raise ValueError('entry_consumer_dirty_release')
        original_hashes[key] = hashlib.sha256(before).hexdigest()
        if before == after:
            continue
        pair = (hashlib.sha256(before).hexdigest(), hashlib.sha256(after).hexdigest())
        if pair in (REVIEWED_ENTRY_CONSUMER_SOURCES.get(name),
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
                    REVIEWED_NATIVE_HANDOFF_INTEGRATION_SOURCES.get(name)):
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
            previous_stopped=False):
    token = _STOPPED_PREPARATION.set(
        (day, int(old_pid), str(Path(previous_root).resolve())) if previous_stopped else None)
    native_token = _NATIVE_PREDECESSOR.set(None)
    try:
        return _prepare(day, old_pid=old_pid, previous_root=previous_root, confirm=confirm,
                        now=now, reseal_postclose_source=reseal_postclose_source,
                        previous_stopped=previous_stopped)
    finally:
        _NATIVE_PREDECESSOR.reset(native_token)
        _STOPPED_PREPARATION.reset(token)


def _prepare(day, *, old_pid, previous_root, confirm, now=None, reseal_postclose_source=False,
             previous_stopped=False):
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
        frozen.extend([Path(source['controller_path']), Path(source['summary_path']), checklist])
        reseal = dict(source_date=source_day, target_date=day, current_source_receipts=source,
                      checklist_path=str(checklist), original_controller_sha256=original_prepared.get('controller_sha256'),
                      original_summary_sha256=original_prepared.get('summary_sha256'), policy_effect='unchanged')
        if historical: reseal['historical_checklist'] = historical
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
            required.update([source['controller_path'], source['summary_path'], reseal['checklist_path']])
        historical_document = None
        if historical_observer:
            # Only an already-consumed historical handoff may disregard edits
            # to the operational checklist. Its sealed snapshot and all other
            # sources remain required. Public verify/consume/activation never
            # take this branch, and the observer binds the live PID separately.
            if not reseal or not reseal.get('historical_checklist') or not consumed_path.exists():
                raise ValueError('intraday_observer_consumed_historical_handoff_required')
            historical_document = reseal['checklist_path']
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
            check = verify(day, commit, now=current)
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
                                 previous_stopped=args.previous_stopped)
            elif args.activate_main_v2:
                result=activate_main_v2(args.target_date,pid=args.pid,confirm=args.confirm)
            elif args.consume:
                result = consume(args.target_date, pid=args.pid)
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
