"""Successor dispatch outside the immutable v4 module pins."""
from src.engine.scalping import reversal_policy_backend as OLD
from src.engine.scalping import reversal_operating_runtime as V5
_ACTIVE = OLD


def configure_bundle(bundle, *, data_root, day):
    global _ACTIVE
    if bundle.get('continuous_reversal',{}).get('schema') == 'continuous_reversal_policy_v5':
        V5.configure(bundle['continuous_reversal'],data_root,day); _ACTIVE = V5
    else:
        OLD.configure_bundle(bundle,data_root=data_root,day=day); _ACTIVE = OLD


def backend(claim=None):
    if _ACTIVE is V5 or (claim or {}).get('backend') == 'operating_v5':
        return V5
    return OLD.backend(claim)


def observe_normalized(*args, **kwargs):
    if _ACTIVE is OLD and OLD.backend() is V5.R:
        return V5.observe_native(*args,**kwargs)
    return _ACTIVE.observe_normalized(*args,**kwargs)


def validate_any_claim(claim, family_sha256, *, now):
    return backend(claim).validate_claim(claim,family_sha256,now=now)


def acknowledge_any(claim, *, status):
    return backend(claim).acknowledge(claim,status=status)
