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
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.automation import runtime_policy_bootstrap as bootstrap
from src.engine.infrastructure.runtime_release_router import selected_release
from src.utils.constants import DATA_DIR
from src.utils.market_day import is_krx_trading_day

KST = ZoneInfo("Asia/Seoul")
CONFIRM = "APPROVED_INTRADAY_POLICY_PRESERVING_RELEASE_HANDOFF"


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read(path):
    value = json.loads(Path(path).read_text())
    if not isinstance(value, dict):
        raise ValueError("intraday_handoff_object_required")
    return value


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


def _checked_bootstrap(day, pid):
    check = bootstrap.verify_bootstrap(day, pid=pid, write=False)
    if check.get("status") != "pass":
        raise ValueError("intraday_bootstrap_invalid:" + ",".join(check.get("findings") or []))
    return check


def prepare(day, *, old_pid, previous_root, confirm, now=None, reseal_postclose_source=False):
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
    check = _checked_bootstrap(day, old_pid)
    prepared_index = DATA_DIR / "runtime/policy_bootstrap/prepared" / day / "latest.json"
    prepared = _read(prepared_index)
    receipt_path = Path(prepared["receipt_path"])
    prepared_root = prepared_index.parent.resolve()
    if (receipt_path.resolve().parent.parent != prepared_root
            or _sha(receipt_path) != prepared.get("receipt_sha256")):
        raise ValueError("intraday_original_prepared_invalid")
    frozen = [bootstrap.env_path(day), bootstrap.manifest_path(day), _preopen_path(day), prepared_index, receipt_path]
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
        if old_checklist and _sha(old_checklist) != expected:
            relative = 'docs/checklists/' + day + '-stage2-todo-checklist.md'
            origin_commit, predecessor = old_commit, None
            if original.get('selected_release_commit') != old_commit:
                inherited = (prior.get('postclose_source_reseal') or {}).get('historical_checklist')
                if inherited:
                    historical_prior, predecessor = _historical_predecessor(day, old_commit, expected)
                    origin_commit = historical_prior['git_commit']
            original_bytes = subprocess.check_output(['git', '-C', str(previous), 'show', origin_commit + ':' + relative])
            if hashlib.sha256(original_bytes).hexdigest() != expected:
                raise ValueError('intraday_original_checklist_git_generation_missing')
            snapshot = _paths(day, commit)[0].parent / (commit + '.historical-checklist.md')
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            if snapshot.exists():
                if snapshot.read_bytes() != original_bytes:
                    raise ValueError('intraday_historical_checklist_snapshot_changed')
            else:
                with snapshot.open('xb') as out:
                    out.write(original_bytes); out.flush(); os.fsync(out.fileno())
            historical = dict(path=str(snapshot), sha256=expected, git_commit=origin_commit,
                              git_path=relative, basis='original_whole_chain_checklist_generation')
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
    if _identity(old_pid) != old_identity:
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
        frozen = payload["frozen_files"]
        required = {str(bootstrap.env_path(day)), str(bootstrap.manifest_path(day)), str(_preopen_path(day)),
                    str(DATA_DIR / "runtime/policy_bootstrap/prepared" / day / "latest.json"),
                    payload["prepared_receipt_path"]}
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
        if set(frozen) != required or any(_sha(name) != sha for name, sha in frozen.items()):
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
    parser.add_argument("--pid", type=int)
    parser.add_argument("--previous-root")
    parser.add_argument("--confirm")
    parser.add_argument('--reseal-postclose-source', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.prepare:
            result = prepare(args.target_date, old_pid=args.old_pid, previous_root=args.previous_root,
                             confirm=args.confirm, reseal_postclose_source=args.reseal_postclose_source)
        elif args.activate_main_v2:
            result=activate_main_v2(args.target_date,pid=args.pid,confirm=args.confirm)
        elif args.consume:
            result = consume(args.target_date, pid=args.pid)
        else:
            result = verify(args.target_date, _selection(require_selected_cwd=False)[1])
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        result = {"status": "fail", "findings": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
