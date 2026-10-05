"""One authorized non-Samsung designation and subsequent fixed-pair comparison.

The existing machine publisher owns the lock and activation. This module never
places orders, changes safety controls, or treats designation as validation.
"""
from copy import deepcopy
from datetime import datetime
from pathlib import Path
import fcntl
import hashlib
import json
import re
from threading import RLock

from src.engine.scalping import entry_strategy_policy as S
from src.engine.scalping import entry_admission_recipe as A
from src.engine.scalping import entry_admission_acceptance as V
from src.engine.scalping import entry_first_signal_exit_research as F

SCHEMA = 'main_machine_operator_designation_v1'
PROOF = 'main_machine_designated_selection_v1'
CONTRACT = 'main_machine_designated_fixed_pair_v1'
TARGET = '2026-10-06'
SCOPE = 'KRX|KRX_REGULAR'
MISSING_FORWARD = 'admission_recipe_forward_date_after_2026_10_02_required'


def seal(value):
    value = {k: v for k, v in value.items() if k != 'artifact_content_sha256'}
    return {**value, 'artifact_content_sha256': S.digest(value)}


def valid_hash(value):
    return isinstance(value, dict) and value == seal(value)


def pair(parent, *, parent_bundle_sha256, request_id):
    if parent.get('entry_admission_recipe') or not re.fullmatch(r'[a-zA-Z0-9_-]{8,100}', request_id):
        raise ValueError('designation_baseline_or_request_invalid')
    return seal(dict(schema=CONTRACT, request_id=request_id, effective_target=TARGET,
        scope=SCOPE, symbol_predicate='exclude_005930', recipe_id=A.RECIPE_ID,
        baseline_policy=deepcopy(parent), candidate_policy=A.candidate_policy(parent),
        baseline_sha256=S.digest(parent), candidate_sha256=S.digest(A.candidate_policy(parent)),
        comparison_reference_bundle_sha256=parent_bundle_sha256))


def validate_pair(value):
    if (not valid_hash(value) or value.get('schema') != CONTRACT
        or value != pair(value['baseline_policy'],
            parent_bundle_sha256=value['comparison_reference_bundle_sha256'], request_id=value['request_id'])):
        raise ValueError('designation_pair_invalid')
    return value


def samsung_equivalent(old, new):
    """Only the exact registered exclude-005930 recipe may differ."""
    return old == new or (not old.get('entry_admission_recipe') and new == A.candidate_policy(old)) or (
        not new.get('entry_admission_recipe') and old == A.candidate_policy(new))


def arm(value, policy):
    validate_pair(value)
    for name in ('baseline', 'candidate'):
        if policy == value[name + '_policy']:
            return name
    raise ValueError('fixed_pair_incumbent_outside_registered_pair')


def make_request(report_path, *, previous, superseded, request_id, authorization, review):
    """Create reviewable content; publication independently checks every binding."""
    from src.engine.scalping import mechanistic_entry_runtime_policy as M
    report_path = Path(report_path)
    report = M._read(report_path)
    p = pair(previous['machine_policy'], parent_bundle_sha256=previous['bundle_sha256'], request_id=request_id)
    return seal(dict(schema=SCHEMA, request_id=request_id, target_date=TARGET,
        publication_date='2026-10-05', source_date=report['target_date'],
        authorization=authorization, review=review, designated_pair=p,
        parent_bundle_sha256=previous['bundle_sha256'],
        parent_machine_policy_sha256=p['baseline_sha256'],
        supersedes_bundle_sha256=superseded['bundle_sha256'],
        automatic_report_path=str(report_path.resolve()),
        automatic_report_file_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        automatic_report_sha256=report['artifact_content_sha256'],
        adoption_basis='operator_designation', validation_status='not_observed',
        evidence_qualified_selection=False, actual_order_submitted=False,
        candidate_policy=p['candidate_policy'], allowed_component_diff=['entry_admission_recipe']))


def validate_request(request, report, parent, *, require_files=False):
    from src.engine.scalping import entry_admission_analysis as H
    if (not valid_hash(request) or request.get('schema') != SCHEMA
        or request.get('target_date') != TARGET or request.get('publication_date') != '2026-10-05'
        or request.get('source_date') != '2026-10-02'
        or request.get('adoption_basis') != 'operator_designation'
        or request.get('validation_status') != 'not_observed'
        or request.get('evidence_qualified_selection') is not False
        or request.get('actual_order_submitted') is not False
        or request.get('allowed_component_diff') != ['entry_admission_recipe']
        or not isinstance(request.get('authorization'), dict)
        or request['authorization'].get('user_instruction') != '계획 실행'
        or not request['authorization'].get('plan_path')
        or not isinstance(request.get('review'), dict)
        or request['review'].get('unresolved_in_scope_defects') != 0
        or request['review'].get('targeted_validation') != 'passed'
        or not request['review'].get('evidence_sha256')):
        raise ValueError('designation_request_invalid')
    p = validate_pair(request['designated_pair'])
    if (request['request_id'] != p['request_id'] or parent != p['baseline_policy']
        or request['parent_machine_policy_sha256'] != S.digest(parent)
        or request['parent_bundle_sha256'] != p['comparison_reference_bundle_sha256']
        or request['candidate_policy'] != p['candidate_policy']
        or not valid_hash(report) or request['automatic_report_sha256'] != report['artifact_content_sha256']
        or report.get('parent_bundle_sha256') != request['parent_bundle_sha256']
        or report.get('parent_machine_policy_sha256') != S.digest(parent)
        or report.get('hurdle_errors') != [MISSING_FORWARD]
        or report.get('candidate_selected') is not False
        or report.get('candidate_train_qualified') is not True
        or report.get('candidate_validation_evaluated') is not False
        or report.get('candidate_policy') is not None
        or report.get('candidate_machine_policy_sha256') != p['candidate_sha256']
        or (report.get('source_receipt') or {}).get('machine_threshold_tuning_input_allowed') is not True):
        raise ValueError('designation_frozen_report_invalid')
    H.validate_report(report['admission_analysis'], parent=parent, target_date=report['target_date'], require_files=require_files)
    V.validate_source(report, require_files=require_files)


def _snapshot_bytes(path, data, M):
    sha = hashlib.sha256(data).hexdigest()
    target = path / 'sources' / (sha + '.json')
    if target.exists():
        if target.read_bytes() != data:
            raise ValueError('designation_source_collision')
    else:
        # Atomic helper preserves JSON semantics; exact physical bytes are kept
        # separately because source_file_sha256 is a byte hash.
        target.parent.mkdir(parents=True, exist_ok=True)
        import os
        import tempfile
        with tempfile.NamedTemporaryFile(dir=target.parent,prefix=target.name+'.',suffix='.tmp',delete=False) as handle:
            temporary=Path(handle.name)
            try:
                handle.write(data); handle.flush(); os.fsync(handle.fileno())
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
        try:
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
        fd = os.open(target.parent, os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    return sha


def _archive(root, bundle, M):
    path = root / 'generations' / (bundle['bundle_sha256'] + '.json')
    if path.exists() and M._read(path) != bundle:
        raise ValueError('designation_generation_collision')
    if not path.exists():
        M._atomic_write_json(path, bundle)


def _bundle(previous, template, source, source_hash, machine, p, *, current, target, disposition):
    result = deepcopy(template)
    result.pop('strategy_activation', None)
    result.update(target_date=target, publication_date=current.date().isoformat(),
        source_date=source.get('source_date', source.get('target_date')),
        source_file_sha256=source_hash, source_artifact_sha256=source['artifact_content_sha256'],
        previous_bundle_sha256=previous['bundle_sha256'], generated_at=current.isoformat(),
        designated_pair=deepcopy(p), machine_disposition=disposition,
        winrate_selection=dict(schema=PROOF, disposition=disposition,
            report_sha256=source['artifact_content_sha256'], policy_version=CONTRACT,
            parent_bundle_sha256=previous['bundle_sha256'], machine_policy_sha256=S.digest(machine)))
    result['machine_policy'] = deepcopy(machine)
    if result.get('all_continuous_adopted'):
        result['scope_policies'][SCOPE]['machine_policy'] = deepcopy(machine)
        result['scope_policies'][SCOPE]['machine_disposition'] = disposition
    result.pop('bundle_sha256', None)
    result['bundle_sha256'] = S.digest(result)
    return result


def _receipt(bundle, status='operator_designation_preserved', report=None):
    return dict(status=status, target_date=bundle['target_date'], bundle_sha256=bundle['bundle_sha256'],
        disposition=bundle['machine_disposition'], machine_policy_sha256=S.digest(bundle['machine_policy']),
        request_id=bundle['designated_pair']['request_id'], current_unchanged=True,
        current_report_sha256=(report or {}).get('artifact_content_sha256'),
        adoption_basis='operator_designation', validation_status='not_observed')


def stage(request_path, *, data_root, now=None):
    """Explicit supersession, CAS and recoverable journal under the existing lock."""
    from src.engine.scalping import mechanistic_entry_runtime_policy as M
    current = (now or datetime.now(M.KST)).astimezone(M.KST)
    request = M._read(Path(request_path))
    root = M.root(data_root)
    root.mkdir(parents=True, exist_ok=True)
    with (root / 'publisher.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        # Read journal before the dated loader: an interrupted replacement must
        # be resumable while normal consumers continue to reject it.
        if not valid_hash(request) or not re.fullmatch(r'[a-zA-Z0-9_-]{8,100}', str(request.get('request_id', ''))):
            raise ValueError('designation_request_invalid')
        journal_path = root / 'designated' / (request['request_id'] + '.json')
        journal = M._read(journal_path) if journal_path.exists() else None
        if journal and journal.get('request_sha256') != request['artifact_content_sha256']:
            raise ValueError('designation_request_reused_with_different_content')
        if journal and journal.get('state') == 'committed':
            existing = M.load(data_root=data_root, target_date=TARGET)
            if not existing or existing['bundle_sha256'] != journal['bundle_sha256']:
                raise ValueError('designation_committed_pointer_changed')
            return _receipt(existing, 'already_staged')
        if not current.date().isoformat() == '2026-10-05':
            raise ValueError('designation_target_window_closed')
        previous = M.load_effective(data_root=data_root, target_date=current.date().isoformat())
        if not previous or previous['bundle_sha256'] != request['parent_bundle_sha256']:
            raise ValueError('designation_parent_cas_failed')
        existing = M._read(root / f'policy_{TARGET}.json')
        M.validate(existing, target_date=TARGET)
        report_bytes = Path(request['automatic_report_path']).read_bytes()
        if hashlib.sha256(report_bytes).hexdigest() != request['automatic_report_file_sha256']:
            raise ValueError('designation_report_file_changed')
        report = json.loads(report_bytes)
        validate_request(request, report, previous['machine_policy'], require_files=True)
        if journal:
            bundle = M._read(root / 'generations' / (journal['bundle_sha256'] + '.json'))
            if existing['bundle_sha256'] not in {request['supersedes_bundle_sha256'], bundle['bundle_sha256']}:
                raise ValueError('designation_recovery_pointer_conflict')
        else:
            if (existing['bundle_sha256'] != request['supersedes_bundle_sha256']
                or existing.get('strategy_activation') or existing.get('designated_pair')
                or existing['machine_policy'] != previous['machine_policy']
                or existing.get('previous_bundle_sha256') != previous['bundle_sha256']):
                raise ValueError('designation_dated_cas_failed')
            M._validate_bundle_sources(existing, data_root)
            _archive(root, previous, M); _archive(root, existing, M)
            prior_bytes=(root / f'policy_{TARGET}.json').read_bytes()
            if json.loads(prior_bytes)!=existing:
                raise ValueError('designation_dated_changed_during_snapshot')
            prior_file_sha=_snapshot_bytes(root,prior_bytes,M)
            automatic_hash = _snapshot_bytes(root, report_bytes, M)
            source_bytes = (json.dumps(request, ensure_ascii=False, indent=2) + '\n').encode()
            source_hash = _snapshot_bytes(root, source_bytes, M)
            bundle = _bundle(previous, existing, request, source_hash, request['candidate_policy'],
                request['designated_pair'], current=current, target=TARGET, disposition='operator_designated')
            bundle['machine_evaluation_source'] = dict(source_date=report['target_date'],
                file_sha256=automatic_hash, artifact_content_sha256=report['artifact_content_sha256'],
                report_scope='main_entry_winrate', terminal_state=report['disposition'])
            bundle['bundle_sha256'] = S.digest({k:v for k,v in bundle.items() if k != 'bundle_sha256'})
            M.validate(bundle, target_date=TARGET)
            _archive(root, bundle, M)
            journal = dict(schema='main_machine_designation_transaction_v1', state='prepared',
                request_sha256=request['artifact_content_sha256'], bundle_sha256=bundle['bundle_sha256'],
                supersedes_bundle_sha256=existing['bundle_sha256'], superseded_file_sha256=prior_file_sha, target_date=TARGET)
            M._atomic_write_json(journal_path, seal(journal))
        validate_bundle(bundle, request, data_root, allow_prepared=True)
        M._atomic_write_json(root / f'policy_{TARGET}.json', bundle)
        journal['state'] = 'committed'
        M._atomic_write_json(journal_path, seal(journal))
        readback = M.load(data_root=data_root, target_date=TARGET)
        if readback != bundle:
            raise ValueError('designation_readback_failed')
        return _receipt(bundle, 'designated_policy_staged', report)


def validate_bundle(bundle, source, data_root, *, allow_prepared=False):
    """Called from the normal loader; archived source hashes are checked there."""
    from src.engine.scalping import mechanistic_entry_runtime_policy as M
    p = validate_pair(bundle['designated_pair'])
    proof = bundle['winrate_selection']
    parent = M._read(M.root(data_root) / 'generations' / (proof['parent_bundle_sha256'] + '.json'))
    M.validate(parent, target_date=parent['target_date'])
    if (not valid_hash(source) or proof.get('schema') != PROOF
        or bundle.get('designated_pair') != source.get('designated_pair')
        or proof.get('report_sha256') != source['artifact_content_sha256']
        or proof.get('policy_version') != CONTRACT
        or parent['bundle_sha256'] != proof['parent_bundle_sha256']
        or proof['parent_bundle_sha256'] != source['parent_bundle_sha256']
        or proof['machine_policy_sha256'] != S.digest(bundle['machine_policy'])):
        raise ValueError('designation_bundle_binding_invalid')
    if source.get('schema') == SCHEMA:
        auto_path = M.root(data_root) / 'sources' / (source['automatic_report_file_sha256'] + '.json')
        if M._source_hash(str(auto_path), M._signature(auto_path)) != source['automatic_report_file_sha256']:
            raise ValueError('designation_automatic_report_hash_invalid')
        validate_request(source, M._read(auto_path), parent['machine_policy'])
        journal = M._read(M.root(data_root) / 'designated' / (p['request_id'] + '.json'))
        staged_hash = (bundle.get('strategy_activation') or {}).get('stage_bundle_sha256', bundle['bundle_sha256'])
        rollback=(bundle.get('strategy_activation') or {}).get('rollback_machine_generation')
        if rollback:
            donor=M._read(M.root(data_root)/'generations'/(rollback+'.json'))
            M.validate(donor,target_date=donor['target_date'])
            if donor['bundle_sha256']!=rollback or donor.get('winrate_selection')!=proof or donor['machine_policy']!=bundle['machine_policy']:
                raise ValueError('designation_rollback_proof_invalid')
            staged_hash=journal.get('bundle_sha256')
        # Auxiliary descendants retain the original dated designation binding.
        if (bundle.get('strategy_activation') or {}).get('schema') in {'main_auxiliary_activation_v1', 'main_auxiliary_operator_prompt_v1'}:
            staged_hash = journal.get('bundle_sha256')
        if (not valid_hash(journal) or journal.get('request_sha256') != source['artifact_content_sha256']
            or journal.get('bundle_sha256') != staged_hash
            or journal.get('supersedes_bundle_sha256') != source['supersedes_bundle_sha256']
            or journal.get('state') not in ({'prepared', 'committed'} if allow_prepared else {'committed'})
            or bundle['machine_policy'] != p['candidate_policy']
            or proof.get('disposition') != 'operator_designated'):
            raise ValueError('designation_transaction_incomplete_or_invalid')
        prior_path=M.root(data_root)/'sources'/(journal['superseded_file_sha256']+'.json')
        if M._source_hash(str(prior_path),M._signature(prior_path))!=journal['superseded_file_sha256']:
            raise ValueError('designation_superseded_bytes_invalid')
        superseded = M._read(M.root(data_root) / 'generations' / (source['supersedes_bundle_sha256'] + '.json'))
        if M._read(prior_path)!=superseded:
            raise ValueError('designation_superseded_bytes_generation_mismatch')
        M.validate(superseded, target_date=TARGET)
        if (superseded['bundle_sha256'] != source['supersedes_bundle_sha256']
            or superseded['machine_policy'] != p['baseline_policy']):
            raise ValueError('designation_superseded_policy_invalid')
        if not bundle.get('strategy_activation') and (bundle['ai_policy'] != superseded['ai_policy']
            or any(bundle['scope_policies'][scope]['ai_policy'] != before['ai_policy']
                for scope,before in (superseded.get('scope_policies') or {}).items())):
            raise ValueError('designation_auxiliary_component_changed')
    else:
        validate_comparison_source(source, parent['machine_policy'], data_root=data_root)
        machine = source['candidate_policy'] if source['disposition'] == 'successor_selected' else parent['machine_policy']
        if bundle['machine_policy'] != machine or proof['disposition'] != source['disposition']:
            raise ValueError('fixed_pair_selected_policy_invalid')
    # Only the KRX machine component is allowed to change. AI can subsequently
    # change through its own existing activation contract, never this stage.
    if not bundle.get('strategy_activation'):
        for scope, before in (parent.get('scope_policies') or {}).items():
            if scope != SCOPE and bundle['scope_policies'][scope]['machine_policy'] != before['machine_policy']:
                raise ValueError('designation_other_scope_changed')
    return bundle


def binding_valid(report, bundle, data_root):
    """An automatic carry report and a designation remain distinct receipts."""
    from src.engine.scalping import mechanistic_entry_runtime_policy as M
    try:
        if (bundle.get('winrate_selection') or {}).get('schema') != PROOF:
            return False
        source = M._read(M.root(data_root) / 'sources' / (bundle['source_file_sha256'] + '.json'))
        M._validate_bundle_sources(bundle, data_root)
        if source.get('schema') == SCHEMA:
            # A refreshed computation is accepted only with the same raw input,
            # pair and absence of any additional automatic rejection reason.
            original = M._read(M.root(data_root) / 'sources' / (source['automatic_report_file_sha256'] + '.json'))
            V.validate_source(report)
            return (report.get('hurdle_errors') == [MISSING_FORWARD]
                and report.get('parent_bundle_sha256') == source['parent_bundle_sha256']
                and report.get('candidate_machine_policy_sha256') == source['designated_pair']['candidate_sha256']
                and report.get('admission_analysis', {}).get('input_capture_sha256') == original['admission_analysis']['input_capture_sha256']
                and report.get('admission_analysis', {}).get('source_manifest') == original['admission_analysis']['source_manifest']
                and report.get('candidate_selected') is False and report.get('candidate_train_qualified') is True)
        return source == report
    except (OSError, ValueError, KeyError, TypeError):
        return False


def preserve(report, *, data_root, target):
    from src.engine.scalping import mechanistic_entry_runtime_policy as M
    bundle = M.load(data_root=data_root, target_date=target)
    if bundle and (bundle.get('winrate_selection') or {}).get('schema') == PROOF:
        if not binding_valid(report, bundle, data_root):
            raise ValueError('designation_refresh_binding_invalid')
        return _receipt(bundle, report=report)
    return None


def record_activation(bundle, *, data_root):
    from src.engine.scalping import mechanistic_entry_runtime_policy as M
    p = bundle.get('designated_pair')
    if not p or bundle['machine_policy'] != p['candidate_policy']:
        return
    path = M.root(data_root) / 'designated' / ('activation_' + p['request_id'] + '.json')
    if path.exists():
        return
    activation = bundle.get('strategy_activation') or {}
    if activation.get('schema') != 'main_entry_winrate_activation_v1':
        return
    M._atomic_write_json(path, seal(dict(schema='main_machine_designated_activation_v1',
        pair_sha256=p['artifact_content_sha256'], bundle_sha256=bundle['bundle_sha256'],
        effective_from=activation['effective_from'], target_date=TARGET,
        actual_pid_consumption=False)))



_GENERATION_CACHE = {}
_GENERATION_CACHE_LOCK = RLock()


def validated_generation(data_root, sha):
    """Validate once per immutable generation; check all dependency signatures.

    Postclose may contain thousands of captures of the same policy. Re-reading
    and re-scoring its full selection report per capture is quadratic work.
    The cache is bounded and propagates dependencies to the normal loader.
    """
    from src.engine.scalping import mechanistic_entry_runtime_policy as M
    if not re.fullmatch(r'[0-9a-f]{64}',str(sha)):
        raise ValueError('fixed_pair_capture_bundle_missing')
    key=(str(Path(data_root).resolve()),sha)
    with _GENERATION_CACHE_LOCK:
        cached=_GENERATION_CACHE.get(key)
        if cached:
            bundle,dependencies=cached
            if any(M._signature(Path(path))!=signature for path,signature in dependencies.items()):
                _GENERATION_CACHE.pop(key,None)
                raise ValueError('fixed_pair_generation_dependency_changed')
        else:
            dependencies={}
            token=M._READ_DEPENDENCIES.set(dependencies)
            try:
                bundle=M._read(M.root(data_root)/'generations'/(sha+'.json'))
                M.validate(bundle,target_date=bundle['target_date'])
                M._validate_bundle_sources(bundle,data_root)
                if bundle['bundle_sha256']!=sha:
                    raise ValueError('fixed_pair_capture_bundle_mismatch')
                if any(M._signature(Path(path))!=signature for path,signature in list(dependencies.items())):
                    raise ValueError('fixed_pair_generation_dependency_changed')
            finally:
                M._READ_DEPENDENCIES.reset(token)
            if len(_GENERATION_CACHE)>=64:
                _GENERATION_CACHE.pop(next(iter(_GENERATION_CACHE)))
            _GENERATION_CACHE[key]=(bundle,dependencies)
        outer=M._READ_DEPENDENCIES.get()
        if outer is not None:
            for path,signature in dependencies.items():
                if outer.setdefault(path,signature)!=signature:
                    raise ValueError('fixed_pair_generation_dependency_changed')
        return bundle

def observation_policy(row, *, data_root, p):
    """Verify P_t and the original action, then label actual post-activation data."""
    from src.engine.scalping import mechanistic_entry_runtime_policy as M
    from src.engine.scalping import entry_setup_evidence as E
    sha = row.get('bundle_sha256')
    if not re.fullmatch(r'[0-9a-f]{64}', str(sha)):
        raise ValueError('fixed_pair_capture_bundle_missing')
    bundle = validated_generation(data_root,sha)
    if bundle['bundle_sha256'] != sha:
        raise ValueError('fixed_pair_capture_bundle_mismatch')
    policy = M.for_cohort(bundle, ('KRX', 'KRX_REGULAR'))['machine_policy']
    actual = E.mechanistic_entry_policy_decision(row['setup_evidence'], policy=policy)
    if actual['action'] != row.get('machine_action'):
        raise ValueError('fixed_pair_captured_action_mismatch')
    stamp = datetime.fromisoformat(row['decision_ts'])
    activation = bundle.get('strategy_activation') or {}
    if stamp.tzinfo is None or (activation and stamp < datetime.fromisoformat(activation['effective_from'])):
        raise ValueError('fixed_pair_capture_before_bundle_activation')
    receipt_path = M.root(data_root) / 'designated' / ('activation_' + p['request_id'] + '.json')
    post = False
    receipt_hash = None
    if receipt_path.exists():
        receipt = M._read(receipt_path)
        if not valid_hash(receipt) or receipt.get('pair_sha256') != p['artifact_content_sha256']:
            raise ValueError('fixed_pair_activation_receipt_invalid')
        active = validated_generation(data_root,receipt['bundle_sha256'])
        if (active['bundle_sha256'] != receipt['bundle_sha256']
            or active['machine_policy'] != p['candidate_policy']
            or (active.get('strategy_activation') or {}).get('effective_from') != receipt['effective_from']):
            raise ValueError('fixed_pair_activation_generation_invalid')
        post = (bool(activation) and stamp >= datetime.fromisoformat(receipt['effective_from'])
                and row['source_date'] >= p['effective_target']
                and bundle.get('designated_pair') == p and policy in (p['baseline_policy'], p['candidate_policy']))
        receipt_hash = receipt['artifact_content_sha256']
    return dict(actual_policy_sha256=S.digest(policy), actual_action=actual['action'],
                post_apply=post, activation_receipt_sha256=receipt_hash)


def evaluate(analysis, p, incumbent, *, target_date):
    validate_pair(p)
    incumbent_arm = arm(p, incumbent)
    challenger = 'baseline' if incumbent_arm == 'candidate' else 'candidate'
    rows = V._rows(analysis, target_date)
    for row in rows:
        if row.get('post_apply') is True and (
            row.get('actual_policy_sha256') not in {p['baseline_sha256'],p['candidate_sha256']}
            or row.get('actual_action') != row.get('captured_action')
            or not re.fullmatch(r'[0-9a-f]{64}',str(row.get('activation_receipt_sha256')))):
            raise ValueError('fixed_pair_post_apply_consumption_unproven')
    rows = [r for r in rows if r.get('post_apply') is True and r['day'] >= p['effective_target']]
    identities = [r['trace'] for r in rows]
    if len(identities) != len(set(identities)):
        raise ValueError('fixed_pair_duplicate_capture')
    rows = F.mask_first_signals(rows, F.first_signal_events(rows))
    dates = sorted({r['day'] for r in rows})
    fields = {'baseline': 'parent_action', 'candidate': 'candidate_action'}
    windows = {}
    for name, selected in [('latest', [r for r in rows if dates and r['day'] == dates[-1]]), ('cumulative', rows)]:
        old, old_rows = V._metrics(selected, fields[incumbent_arm])
        new, new_rows = V._metrics(selected, fields[challenger])
        windows[name] = dict(incumbent=old, challenger=new, hurdles=V._hurdles(old, new, 10),
                            retention_diagnostic=V._retention(old_rows, new_rows))
    errors = [name + ':' + k for name, w in windows.items() for k, ok in w['hurdles'].items() if not ok]
    if not dates:
        errors.insert(0, 'post_apply_observations_not_observed')
    return dict(contract=CONTRACT, pair_sha256=p['artifact_content_sha256'], incumbent_arm=incumbent_arm,
        challenger_arm=challenger, latest_date=dates[-1] if dates else None, cumulative_dates=dates,
        latest_included_in_cumulative=True, windows_independent=False, windows=windows,
        observation_manifest_sha256=S.digest(sorted(rows, key=lambda r: (r['day'], r['trace']))),
        candidate_selected=not errors, hurdle_errors=errors, success_retention_role='diagnostic_only',
        coverage_role='diagnostic_only', validation_status='observed' if dates else 'not_observed')


def apply(report, analysis, parent, p):
    result = deepcopy(report)
    comparison = evaluate(analysis, p, parent, target_date=report['target_date'])
    proposed = p[comparison['challenger_arm'] + '_policy']
    result.pop('acceptance_contract', None)
    result.update(fixed_pair_contract=CONTRACT, designated_pair=deepcopy(p), fixed_pair_comparison=comparison,
        selection_objective_version=CONTRACT, opportunity_identity_contract=V.UNIT,
        candidate_computed=bool(analysis['observations']), candidate_train_qualified=False,
        candidate_validation_evaluated=bool(comparison['cumulative_dates']),
        candidate_selected=comparison['candidate_selected'], candidate_evaluated=bool(comparison['cumulative_dates']),
        fresh_validation=comparison['validation_status'],
        candidate_machine_policy_sha256=S.digest(proposed),
        candidate_policy=deepcopy(proposed) if comparison['candidate_selected'] else None,
        disposition='successor_selected' if comparison['candidate_selected'] else 'incumbent_carried',
        hurdle_errors=comparison['hurdle_errors'], train_dates=[], holdout_dates=[],
        policy_by_scope={SCOPE: deepcopy(proposed)} if comparison['candidate_selected'] else {},
        baseline={w: x['incumbent'] for w,x in comparison['windows'].items()},
        candidate={w: x['challenger'] for w,x in comparison['windows'].items()},
        adoption_basis='fixed_pair_post_apply_comparison',
        comparison_reference_sha256=p['baseline_sha256'], activation_parent_sha256=S.digest(parent))
    result['policy_sha256'] = S.digest(result['policy_by_scope'])
    return seal(result)


def validate_comparison_source(source, parent, *, data_root=None, require_files=False):
    from src.engine.scalping import entry_admission_analysis as H
    if (not valid_hash(source) or source.get('fixed_pair_contract') != CONTRACT
        or source.get('selection_objective_version') != CONTRACT
        or source.get('selection_basis') != 'win_rate_only'
        or source.get('parent_machine_policy_sha256') != S.digest(parent)):
        raise ValueError('fixed_pair_source_invalid')
    from src.engine.scalping import mechanistic_entry_runtime_policy as M
    excluded=source.get('excluded_attempt_counts') or {}
    situations=source.get('situation_attempt_counts') or {}
    counts=[source.get(k) for k in ('input_attempt_count','accepted_attempt_count','source_contract_excluded_count')]
    if (source.get('schema')!='main_entry_winrate_policy_report_v1'
        or source.get('report_scope')!='main_entry_winrate' or source.get('candidate_kind')!='admission_recipe'
        or source.get('candidate_recipe_id')!=A.RECIPE_ID
        or any(type(v) is not int or v<0 for v in counts+list(excluded.values())+list(situations.values()))
        or counts[1]+counts[2]+sum(excluded.values())!=counts[0] or sum(situations.values())!=counts[1]
        or not M.winrate_market_census_valid(source)
        or (source.get('source_receipt') or {}).get('target_date')!=source.get('target_date')
        or (source.get('candidate_selected') is True and (source.get('source_receipt') or {}).get('machine_threshold_tuning_input_allowed') is not True)
        or any(not re.fullmatch(r'[0-9a-f]{64}',str(source.get(k))) for k in ('source_contract_sha256','evaluated_attempt_manifest_sha256'))):
        raise ValueError('fixed_pair_source_census_or_authority_invalid')
    p = validate_pair(source['designated_pair'])
    H.validate_report(source['admission_analysis'], parent=parent, target_date=source['target_date'], require_files=require_files)
    expected = apply(source, source['admission_analysis'], parent, p)
    if expected != source:
        raise ValueError('fixed_pair_source_recomputation_mismatch')
    if source['admission_analysis'].get('designated_pair') != p:
        raise ValueError('fixed_pair_analysis_pair_mismatch')
    if data_root is not None:
        from src.engine.scalping import mechanistic_entry_runtime_policy as M
        receipt_path = M.root(data_root)/'designated'/('activation_'+p['request_id']+'.json')
        post_rows = [r for r in source['admission_analysis']['observations'] if r.get('post_apply') is True]
        if post_rows:
            receipt = M._read(receipt_path)
            if not valid_hash(receipt) or receipt.get('pair_sha256') != p['artifact_content_sha256']:
                raise ValueError('fixed_pair_activation_unproven')
            for row in post_rows:
                actual = validated_generation(data_root,row['source_bundle_sha256'])
                effective = (actual.get('strategy_activation') or {}).get('effective_from')
                if (not effective or actual['bundle_sha256'] != row['source_bundle_sha256']
                    or actual.get('designated_pair') != p
                    or S.digest(actual['machine_policy']) != row['actual_policy_sha256']
                    or datetime.fromisoformat(row['ts']) < max(datetime.fromisoformat(effective),datetime.fromisoformat(receipt['effective_from']))
                    or row['activation_receipt_sha256'] != receipt['artifact_content_sha256']):
                    raise ValueError('fixed_pair_observation_generation_invalid')
    return expected


def stage_comparison(source_path, *, data_root, publication_day=None, now=None):
    from src.engine.scalping import mechanistic_entry_runtime_policy as M
    current = (now or datetime.now(M.KST)).astimezone(M.KST)
    publication = publication_day or current.date().isoformat()
    source = M._read(Path(source_path)); root = M.root(data_root)
    with (root / 'publisher.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        previous = M.load_effective(data_root=data_root, target_date=publication)
        if (not previous or source.get('parent_bundle_sha256') != previous['bundle_sha256']
            or previous.get('designated_pair') != source.get('designated_pair')
            or source.get('publication_date', publication) != publication
            or not TARGET <= source['target_date'] <= publication <= current.date().isoformat()):
            raise ValueError('fixed_pair_stage_parent_or_date_invalid')
        validate_comparison_source(source, previous['machine_policy'], data_root=data_root, require_files=True)
        target = M.next_target(publication)
        existing = M.load(data_root=data_root, target_date=target)
        if existing and existing.get('winrate_selection'):
            if existing['winrate_selection'].get('report_sha256') == source['artifact_content_sha256']:
                return dict(status='already_staged', target_date=target, bundle_sha256=existing['bundle_sha256'], disposition=source['disposition'])
            raise ValueError('fixed_pair_dated_generation_already_staged')
        data = Path(source_path).read_bytes()
        if json.loads(data) != source:
            raise ValueError('fixed_pair_source_changed')
        source_hash = _snapshot_bytes(root, data, M)
        machine = source['candidate_policy'] or previous['machine_policy']
        template = existing or previous
        if template['machine_policy'] != previous['machine_policy']:
            raise ValueError('fixed_pair_existing_machine_conflict')
        bundle = _bundle(previous, template, source, source_hash, machine, source['designated_pair'],
            current=current.replace(year=int(publication[:4]), month=int(publication[5:7]), day=int(publication[8:10])),
            target=target, disposition=source['disposition'])
        bundle['machine_evaluation_source'] = dict(source_date=source['target_date'], file_sha256=source_hash,
            artifact_content_sha256=source['artifact_content_sha256'], report_scope='main_entry_winrate', terminal_state=source['disposition'])
        bundle['bundle_sha256'] = S.digest({k:v for k,v in bundle.items() if k != 'bundle_sha256'})
        _archive(root, previous, M); M.validate(bundle, target_date=target); M._validate_bundle_sources(bundle, data_root)
        _archive(root, bundle, M); M._atomic_write_json(root / f'policy_{target}.json', bundle)
        return dict(status='staged', target_date=target, bundle_sha256=bundle['bundle_sha256'], disposition=source['disposition'])
