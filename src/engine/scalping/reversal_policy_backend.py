"""Explicit dispatch between immutable reversal and typed path consumers."""
from src.engine.scalping import reversal_registered_runtime as V3
from src.engine.scalping import reversal_path_runtime as V4

_ACTIVE = V3


def configure_bundle(bundle, data_root, day):
    global _ACTIVE
    family = (bundle or {}).get('continuous_reversal')
    if family and family.get('schema') not in {'continuous_reversal_policy_v1','continuous_reversal_policy_v2','continuous_reversal_policy_v3','continuous_reversal_policy_v4'}:
        raise ValueError('continuous_reversal_backend_schema_unsupported')
    if family and family.get('schema') == 'continuous_reversal_policy_v4':
        V4.configure(family)
        # Reuse same-process, exact native session anchors already restored by
        # the v3 consumer. Roots still warm up; past signals are never emitted.
        with V3._LOCK:
            restored=day in V3._RESTORED_DAYS
            anchors={k:list(v) for k,v in V3._ANCHORS.items() if k[-1]==day} if restored else {}
            empty=day in V3._EMPTY_PREFIX_DAYS
        if restored:
            with V4._LOCK:
                V4._ANCHORS.update(anchors)
                for key,state in V4._STATES.items():
                    if key[-1]==day:state.session_anchor=V4._ANCHORS.get(key)
                V4._RESTORED_DAYS.add(day)
                if empty:V4._EMPTY_PREFIX_DAYS.add(day)
        V4.restore_session_anchors(data_root, day)
        _ACTIVE = V4
    else:
        V3.configure_bundle(bundle, data_root, day)
        _ACTIVE = V3


def backend(claim=None):
    if claim is not None:
        if claim.get('backend') not in {None,'registered_v3','registered_v4'}:
            raise ValueError('continuous_reversal_claim_backend_unsupported')
        return V4 if claim.get('backend') == 'registered_v4' else V3.backend(claim)
    return V4 if _ACTIVE is V4 else V3.backend()


def observe_normalized(symbol, session, envelope):
    return _ACTIVE.observe_normalized(symbol, session, envelope)


def validate_any_claim(claim, family_sha256, *, now):
    return backend(claim).validate_claim(claim, family_sha256, now=now)


def acknowledge_any(claim, *, status):
    return backend(claim).acknowledge(claim, status=status)
