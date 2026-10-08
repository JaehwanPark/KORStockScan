"""Current version dispatch outside all immutable v4/v5 execution pins."""
from src.engine.scalping import reversal_operating_backend as OLD
from src.engine.scalping import reversal_extended_runtime as V6
_ACTIVE=OLD


def configure_bundle(bundle,*,data_root,day):
    global _ACTIVE
    if bundle.get('continuous_reversal',{}).get('schema')=='continuous_reversal_policy_v6':
        V6.configure(bundle['continuous_reversal'],data_root,day);_ACTIVE=V6
    else:
        OLD.configure_bundle(bundle,data_root=data_root,day=day);_ACTIVE=OLD


def backend(claim=None):
    if _ACTIVE is V6 or (claim or {}).get('backend')=='operating_v6':return V6
    return OLD.backend(claim)


def observe_normalized(*args,**kwargs):return _ACTIVE.observe_normalized(*args,**kwargs)
def validate_any_claim(claim,family_sha256,*,now):return backend(claim).validate_claim(claim,family_sha256,now=now)
def acknowledge_any(claim,*,status):return backend(claim).acknowledge(claim,status=status)
