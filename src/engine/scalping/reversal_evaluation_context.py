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


def _extra_paths(data_root, day, commit):
    from src.engine.automation import intraday_release_handoff as H
    from src.engine.scalping import reversal_auxiliary_intraday as I
    return [Path(data_root).resolve().parent / 'data/runtime/runtime_release_selection.json',
            I.root(data_root) / 'current.json', Path(I.__file__), Path(__file__),
            *H._paths(day, commit),
            N.root(data_root) / 'consumed' / day / (str(os.getpid()) + '.json'),
            I.root(data_root) / 'consumed' / day / (str(os.getpid()) + '.json')]


def _identities(paths):
    with N.signature_pass():
        return {str(p): N._signature(p) if p.exists() else None for p in paths}


def prepare(*, data_root, day):
    """Obtain one trusted immutable view and prepare its current consumer."""
    global _CONFIGURED, _CONSUMED
    from src.engine.automation import intraday_release_handoff as H
    from src.engine.infrastructure.runtime_release_router import selected_release
    from src.engine.scalping import reversal_current_backend as D
    from src.engine.scalping import reversal_auxiliary_intraday as I
    started = time.perf_counter()
    with N.verified_evaluation(data_root=data_root, target_date=day) as bundle:
        if not bundle or bundle.get('continuous_reversal', {}).get('schema') not in {
                'continuous_reversal_policy_v5', 'continuous_reversal_policy_v6'}:
            return bundle
        selected, commit = selected_release(Path(data_root).resolve().parent)
        identity = H._identity(os.getpid())
        if identity['cwd'] != str(selected / 'src'):
            raise ValueError('auxiliary_pid_release_mismatch')
        key = (str(Path(data_root).resolve()), day, bundle['bundle_sha256'],
               identity['pid'], identity['start_ticks'], identity['cwd'], commit)
        if not _LOCK.acquire(timeout=1.0):
            raise ValueError('machine_policy_configuration_in_progress')
        try:
            configured = _CONFIGURED
            # Keep a strong reference: object identity cannot be recycled into
            # a new verification generation after eviction/failure.
            if (configured is None or configured[0] != key or configured[1] is not bundle
                    or getattr(D.backend(), '_GENERATION', None) != bundle['continuous_reversal'].get('family_sha256')):
                _CONFIGURED = None
                D.configure_bundle(bundle, data_root=data_root, day=day)
                _CONFIGURED = (key, bundle)
            extra = _identities(_extra_paths(data_root, day, commit))
            consumed = _CONSUMED
            if (consumed is None or consumed[0] != key or consumed[1] is not bundle
                    or consumed[2] != extra or not N.dependencies_unchanged(consumed[3])):
                _CONSUMED = None
                dependencies = {}
                token = N._READ_DEPENDENCIES.set(dependencies)
                try:
                    if commit != bundle['continuous_reversal'].get('release_commit'):
                        # The legacy reader has a process-lifetime handoff set.
                        # A changed handoff must not hide behind that old set.
                        path, consumed_path = H._paths(day, commit)
                        handoff = H.verify(day, commit)
                        consumed_receipt = H._read(consumed_path)
                        if (handoff.get('status') != 'pass'
                                or consumed_receipt.get('actual_pid_consumed') is not True
                                or consumed_receipt.get('pid_identity') != identity
                                or consumed_receipt.get('handoff_sha256') != H._sha(path)):
                            raise ValueError('auxiliary_base_code_handoff_missing')
                    I.record_pid_consumption(data_root, bundle)
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
            from src.engine.monitoring.runtime_performance import observe
            observe('policy_prepare', time.perf_counter() - started,
                    generation=bundle['bundle_sha256'])
