"""Runtime orchestration outside frozen policy pins; no decision result cache.

The loader remains the policy/source authority. Only successful configuration
and same-PID consumption are idempotent. Every evaluation checks dependencies;
AI and submit callers continue using their independent validation boundaries.
"""
import os
import time
from pathlib import Path
from threading import Lock

from src.engine.scalping import mechanistic_entry_runtime_policy as N

_LOCK = Lock()
_CONFIGURED = None
_CONSUMED = None


def _prepared_v6_claim(policy, active, *, data_root, day):
    """Reuse verified static configuration; validate native eligibility anew.

    None selects the original validator when no loader-owned, consumed view
    exists. No native signal snapshot or decision is cached here.
    """
    from src.engine.scalping import reversal_current_backend as D
    from src.engine.scalping import reversal_extended_union as A
    view = N._VERIFIED_EVALUATION.get()
    if (not isinstance(active, N._FrozenDict) or view is None
            or view[:2] != (str(Path(data_root).absolute()), day) or view[2] is not active):
        return None
    with _LOCK:
        eligible = (_CONFIGURED is not None and _CONSUMED is not None
                    and _CONFIGURED[1] is active and _CONSUMED[1] is active
                    and _CONFIGURED[0] == _CONSUMED[0])
    if not eligible:
        return None
    # Recheck source dependencies, current selection, PID/start/cwd, handoff,
    # auxiliary consumption and backend generation at this final boundary.
    if prepare(data_root=data_root, day=day) is not active:
        raise ValueError('reversal_scope_execution_changed')
    with _LOCK:
        if (_CONFIGURED is None or _CONSUMED is None or _CONFIGURED[1] is not active
                or _CONSUMED[1] is not active or _CONFIGURED[0] != _CONSUMED[0]):
            raise ValueError('reversal_scope_execution_changed')
        family = active.get('continuous_reversal') or {}
        if family.get('schema') != 'continuous_reversal_policy_v6':
            return None
        if getattr(D.backend(), '_GENERATION', None) != family['family_sha256']:
            raise ValueError('reversal_scope_execution_changed')
        assessment = policy['continuous_reversal_assessment']
        cell = family['machine_cells'][assessment['cell_key']]['routes'][assessment['route']]
        if (cell['scope_execution_hash'] != assessment['scope_execution_hash']
                or cell['backend'] != 'union_v6'):
            raise ValueError('reversal_scope_execution_changed')
        snapshot = D.validate_any_claim(policy['continuous_reversal_claim'],
                                        family['family_sha256'], now=time.time())
        remaining = {bid + ':' + A.definition_hash(bid) for bid in snapshot[0]['branch_signals']}
        valid = sorted(remaining.intersection(assessment['matched_policy_refs']))
        if not valid:
            raise ValueError('reversal_all_requested_signals_invalidated')
        return valid


def validate_submit(data_root,fields,*,now,check_generation=False):
    """Use one fresh immutable view for independent final submit validators.

    Never share this view across provider/order I/O. The original generation
    validator still runs; its nested load avoids copying the whole policy.
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from contextlib import ExitStack
    from src.engine.monitoring.runtime_performance import entry_stage
    from src.engine.scalping import reversal_auxiliary_intraday as auxiliary
    started = time.perf_counter()
    assessment=fields.get('entry_mechanistic_policy_decision') or {}
    expected = (fields.get('machine_bundle_sha256') or fields.get('policy_bundle_hash')) if check_generation else None
    if not assessment.get('auxiliary_registry_sha256') and not expected:return
    day=datetime.fromtimestamp(now,ZoneInfo('Asia/Seoul')).date().isoformat()
    loaded = checked = None
    active = None
    try:
        with N.signature_pass(),ExitStack() as boundary:
            with entry_stage('entry_submit_native_load'):
                active=boundary.enter_context(N.verified_evaluation(data_root=Path(data_root),target_date=day))
            loaded = time.perf_counter()
            if assessment.get('auxiliary_registry_sha256'):
                with entry_stage('entry_submit_auxiliary'):
                    checked = now + max(0., time.perf_counter() - started)
                    auxiliary.validate_decision(data_root,dict(continuous_reversal_assessment=assessment),active,now=checked)
            if expected:
                with entry_stage('entry_submit_generation'):
                    generation = N.validate_attempt_generation(expected, data_root=Path(data_root),
                        now=datetime.fromtimestamp(now + max(0.,time.perf_counter()-started),ZoneInfo('Asia/Seoul')))
                    if not generation['allowed']:
                        raise ValueError('initial_send_policy_generation_changed')
    except (OSError,ValueError,KeyError,TypeError) as exc:
        # Enrich the existing terminal, retaining the original reason. A generic
        # frozen-validator error alone does not prove a policy generation change.
        exc.entry_submit_revalidation = dict(
            entered_epoch=now, checked_epoch=checked,
            native_load_ms=None if loaded is None else max(0.,loaded-started)*1000,
            elapsed_ms=max(0.,time.perf_counter()-started)*1000,
            original_signal_epoch=(assessment.get('event') or {}).get('epoch'),
            expected_bundle_sha256=expected, current_bundle_sha256=(active or {}).get('bundle_sha256'))
        raise


def validate_before_provider(policy, *, data_root, model):
    """Fresh final guards on one loader-owned view, before any provider I/O.

    This pass only shares ancestor resolution and avoids materializing a full
    mutable bundle for read-only guards. Native claim, scope, registry, model,
    overlay and revocation validators still run at this independent boundary.
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from contextlib import ExitStack
    from src.engine.monitoring.runtime_performance import entry_stage, timed_entry_call
    from src.engine.scalping import reversal_auxiliary_intraday as I
    assessment = policy['continuous_reversal_assessment']
    version = assessment.get('policy_version')
    if version == 'continuous_reversal_policy_v6':
        from src.engine.scalping.continuous_reversal_policy_v6 import validate_active_claim
    elif version == 'continuous_reversal_policy_v5':
        from src.engine.scalping.continuous_reversal_policy_v5 import validate_active_claim
    else:
        raise ValueError('reversal_pre_provider_version_unsupported')
    day = datetime.now(ZoneInfo('Asia/Seoul')).date().isoformat()
    with N.signature_pass(), ExitStack() as boundary:
        # Keep pointer and dependency checks at entry and exit. The immutable
        # view and this synchronous pass never escape to SDK or order callers.
        with entry_stage('entry_native_load'):
            active = boundary.enter_context(N.verified_evaluation(data_root=data_root, target_date=day))
        remaining = (timed_entry_call('entry_native_claim', _prepared_v6_claim,
                                      policy, active, data_root=data_root, day=day)
                     if version == 'continuous_reversal_policy_v6' else None)
        if remaining is None:
            remaining = timed_entry_call('entry_native_claim', validate_active_claim,
                                         policy, active, now=time.time())
        if set(remaining) != set(assessment['matched_policy_refs']):
            raise ValueError('reversal_request_signal_set_changed_before_send')
        registered = timed_entry_call('entry_native_auxiliary', I.validate_decision,
                                      data_root, policy, active, now=time.time())
        if assessment.get('auxiliary_registry_sha256'):
            if not isinstance(registered, dict):
                raise ValueError('auxiliary_registered_definition_missing')
            if model != registered['model']:
                raise ValueError('auxiliary_registered_model_mismatch')
        return remaining


def _extra_paths(data_root, day, commit):
    from src.engine.automation import intraday_release_handoff as H
    from src.engine.scalping import reversal_auxiliary_intraday as I
    return [Path(data_root).resolve().parent / 'data/runtime/runtime_release_selection.json',
            I.root(data_root) / 'current.json', Path(I.__file__), Path(__file__),
            *H._paths(day, commit),
            Path(data_root) / 'runtime/release_transitions' / day / commit / 'native-predecessor.json',
            Path(data_root) / 'runtime/release_transitions' / day / commit / 'selection-before.json',
            N.root(data_root) / 'consumed' / day / (str(os.getpid()) + '.json'),
            I.root(data_root) / 'consumed' / day / (str(os.getpid()) + '.json')]


def _identities(paths):
    with N.signature_pass():
        return {str(p): N._signature(p) if p.exists() else None for p in paths}


def prepare(*, data_root, day):
    global _CONFIGURED, _CONSUMED
    from src.engine.monitoring.runtime_performance import policy_validation
    with policy_validation('policy_prepare') as facts:
        facts.update(target_date=day)
        allow_retry=N._VERIFIED_EVALUATION.get() is None
        # Share ancestor resolution only inside this synchronous validation. Every
        # file signature is still read, and the pass rechecks symlink/dir custody.
        # Never extend the pass across provider I/O or the next evaluation boundary.
        for attempt in range(2):
            facts['attempt_count'] = attempt+1
            try:
                with N.signature_pass():
                    result = _prepare_verified(data_root=data_root, day=day)
                    facts['bundle_sha256'] = result.get('bundle_sha256') if isinstance(result, dict) else None
                    return result
            except BaseException as exc:
                cleared=False
                if _LOCK.acquire(blocking=False):
                    try:
                        _CONFIGURED = _CONSUMED = None
                        cleared=True
                    finally:
                        _LOCK.release()
                if (attempt==0 and allow_retry and cleared and isinstance(exc,ValueError)
                        and str(exc)=='machine_policy_consumer_source_changed'):
                    facts['retry_reason'] = str(exc)
                    # Launcher PID attestation can publish the selector during
                    # first consumption. Discard that entire pass and validate
                    # every source, handoff and guard afresh exactly once. No old
                    # view, receipt or decision survives into the retry.
                    continue
                raise


def configure_policy_content(bundle, *, data_root, day, read_only=False):
    """Shared in-memory backend setup; never attests a runtime PID."""
    from src.engine.scalping import reversal_current_backend as D
    if bundle and bundle.get('continuous_reversal', {}).get('schema') in {
            'continuous_reversal_policy_v5', 'continuous_reversal_policy_v6'}:
        if read_only:
            D.configure_bundle(bundle, data_root=data_root, day=day, read_only=True)
        else:
            D.configure_bundle(bundle, data_root=data_root, day=day)
    return bundle


def prepare_policy_loading(*, data_root, day, preparation=False):
    """Load native content without activating a pointer or recording consumption.

    Preparation uses the native dated candidate reader, whose provenance and
    code validators remain mandatory. The live reader still requires current
    activation. Neither branch changes the observed clock.
    """
    if preparation:
        bundle = N.load(data_root=Path(data_root), target_date=day)
        return configure_policy_content(bundle, data_root=data_root, day=day, read_only=True)
    with N.verified_evaluation(data_root=data_root, target_date=day) as bundle:
        return configure_policy_content(bundle, data_root=data_root, day=day)


def _prepare_verified(*, data_root, day):
    """Obtain one trusted immutable view and prepare its current consumer."""
    global _CONFIGURED, _CONSUMED
    from src.engine.automation import intraday_release_handoff as H
    from src.engine.infrastructure.runtime_release_router import selected_release
    from src.engine.scalping import reversal_current_backend as D
    from src.engine.scalping import reversal_auxiliary_intraday as I
    from src.engine.monitoring.runtime_performance import observe
    started = time.perf_counter()
    with N.verified_evaluation(data_root=data_root, target_date=day) as bundle:
        observe('policy_load', time.perf_counter() - started)
        if not bundle or bundle.get('continuous_reversal', {}).get('schema') not in {
                'continuous_reversal_policy_v5', 'continuous_reversal_policy_v6'}:
            return bundle
        release_started = time.perf_counter()
        selected, commit = selected_release(Path(data_root).resolve().parent)
        identity = H._identity(os.getpid())
        observe('policy_release_check', time.perf_counter() - release_started)
        if identity['cwd'] != str(selected / 'src'):
            raise ValueError('auxiliary_pid_release_mismatch')
        key = (str(Path(data_root).resolve()), day, bundle['bundle_sha256'],
               identity['pid'], identity['start_ticks'], identity['cwd'], commit)
        lock_started = time.perf_counter()
        acquired = _LOCK.acquire(timeout=1.0)
        from src.engine.monitoring.runtime_performance import policy_validation
        with policy_validation('policy_consumer') as facts:
            facts.update(bundle_sha256=bundle['bundle_sha256'], commit=commit,
                         lock_wait_seconds=time.perf_counter()-lock_started)
            if not acquired:
                raise ValueError('machine_policy_configuration_in_progress')
            consumer_started = time.perf_counter()
            try:
                configured = _CONFIGURED
                facts['configured_reused'] = False
                # Keep a strong reference: object identity cannot be recycled into
                # a new verification generation after eviction/failure.
                if (configured is None or configured[0] != key or configured[1] is not bundle
                        or getattr(D.backend(), '_GENERATION', None) != bundle['continuous_reversal'].get('family_sha256')):
                    _CONFIGURED = None
                    configured_started = time.perf_counter()
                    try:
                        configure_policy_content(bundle, data_root=data_root, day=day)
                    finally:
                        facts['configuration_seconds'] = time.perf_counter()-configured_started
                    _CONFIGURED = (key, bundle)
                facts['configured_reused'] = configured is _CONFIGURED
                identities_started = time.perf_counter()
                extra = _identities(_extra_paths(data_root, day, commit))
                facts['extra_identity_seconds'] = time.perf_counter()-identities_started
                consumed = _CONSUMED
                reason = ('cold' if consumed is None else 'identity_changed' if consumed[0] != key
                          else 'bundle_view_changed' if consumed[1] is not bundle
                          else 'extra_dependency_changed' if consumed[2] != extra
                          else 'dependency_changed' if not N.dependencies_unchanged(consumed[3]) else None)
                facts.update(cache_status='miss' if reason else 'hit', miss_reason=reason)
                if reason:
                    _CONSUMED = None
                    dependencies = {}
                    token = N._READ_DEPENDENCIES.set(dependencies)
                    try:
                        if commit != bundle['continuous_reversal'].get('release_commit'):
                            # The legacy reader has a process-lifetime handoff set.
                            # A changed handoff must not hide behind that old set.
                            path, consumed_path = H._paths(day, commit)
                            handoff_started = time.perf_counter()
                            try:
                                handoff = H.verify(day, commit)
                                consumed_receipt = H._read(consumed_path)
                                if (handoff.get('status') != 'pass'
                                        or consumed_receipt.get('actual_pid_consumed') is not True
                                        or consumed_receipt.get('pid_identity') != identity
                                        or consumed_receipt.get('handoff_sha256') != H._sha(path)):
                                    raise ValueError('auxiliary_base_code_handoff_missing')
                            finally:
                                facts['handoff_verify_seconds'] = time.perf_counter()-handoff_started
                        consumption_started = time.perf_counter()
                        try:
                            I.record_pid_consumption(data_root, bundle)
                        finally:
                            facts['consumption_record_seconds'] = time.perf_counter()-consumption_started
                    finally:
                        N._READ_DEPENDENCIES.reset(token)
                    after = _identities(_extra_paths(data_root, day, commit))
                    # Receipt creation is expected; source/selector changes are not.
                    if any(extra[p] != after[p] for p in list(extra)[:-2]):
                        raise ValueError('machine_policy_consumer_source_changed')
                    if not N.dependencies_unchanged(dependencies):
                        raise ValueError('machine_policy_consumer_dependency_changed')
                    _CONSUMED = (key, bundle, after, dependencies)
                return bundle
            finally:
                _LOCK.release()
                observe('policy_consumer_check', time.perf_counter() - consumer_started)
                observe('policy_prepare', time.perf_counter() - started,
                        generation=bundle['bundle_sha256'])
