"""Explicit Samsung research migration across an exclude-005930 designation.

Original frozen artifacts and original kernels remain evidence. A migration is
accepted only for a sealed replay showing identical Samsung actions and guards.
"""
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from src.engine.scalping import entry_strategy_policy as S
from src.engine.scalping import entry_admission_analysis as H
from src.engine.scalping import entry_designated_policy as D

SCHEMA = 'samsung_component_kernel_migration_v1'


def decision_projection(value):
    """Remove provenance hashes and the inert exclude-005930 receipt only."""
    value=deepcopy(value)
    value.pop('admission_recipe',None);value.pop('admission_recipe_trigger_pass',None)
    def visit(item):
        if isinstance(item,dict):
            return {k:visit(v) for k,v in item.items() if k not in {'policy_sha256','parent_sha256'}}
        if isinstance(item,list):return [visit(v) for v in item]
        return item
    return visit(value)


def path(root,frozen):
    return Path(root)/'data/report/samsung_policy_compatibility'/(S.digest(frozen)+'.json')



def current_kernels(frozen, root):
    original=frozen.get('kernel_manifest',frozen.get('replay_dependency_seals',{}))
    project=Path(__file__).resolve().parents[3]
    result={}
    for key in original:
        source=Path(key)
        if not source.is_absolute():source=Path(__file__).with_name(key)
        elif source.is_relative_to(Path(root)/'src'):source=project/source.relative_to(root)
        result[key]=H.file_sha(source)
    return result

def validate(root,frozen,current_kernels):
    from src.engine.scalping import mechanistic_entry_runtime_policy as M
    value=M._read(path(root,frozen))
    old=frozen.get('kernel_manifest',frozen.get('replay_dependency_seals'))
    if (not D.valid_hash(value) or value.get('schema')!=SCHEMA
        or value.get('frozen_sha256')!=S.digest(frozen) or value.get('old_kernels')!=old
        or value.get('new_kernels')!=current_kernels
        or value.get('migration_kernel_sha256')!=H.file_sha(__file__) or value.get('old_parent')!=frozen['parent_policy']
        or not D.samsung_equivalent(value['old_parent'],value['new_parent'])
        or value['old_parent']==value['new_parent'] or value.get('runtime_apply_allowed') is not False):
        raise ValueError('samsung_kernel_migration_invalid')
    parity=M._read(Path(value['parity_path']))
    if (H.file_sha(value['parity_path'])!=value['parity_file_sha256']
        or not D.valid_hash(parity) or parity.get('observation_count')!=519
        or parity.get('old_parent_sha256')!=S.digest(value['old_parent'])
        or parity.get('new_parent_sha256')!=S.digest(value['new_parent'])
        or parity.get('action_guard_difference_count')!=0
        or len(parity.get('raw_manifest',[]))!=519
        or len({r['trace'] for r in parity['raw_manifest']})!=519):
        raise ValueError('samsung_migration_parity_invalid')
    for entry in value['old_kernel_archives']:
        if old.get(entry['key'])!=entry['sha256'] or H.file_sha(entry['path'])!=entry['sha256']:
            raise ValueError('samsung_migration_old_kernel_unavailable')
    if {r['key'] for r in value['old_kernel_archives']}!=set(old):
        raise ValueError('samsung_migration_old_kernel_coverage_invalid')
    return value


def effective_policy(root,frozen,*,bundle):
    from src.engine.scalping import mechanistic_entry_runtime_policy as M
    scoped=M.for_cohort(bundle,('KRX','KRX_REGULAR')) or {}
    policy=scoped.get('machine_policy')
    if not isinstance(policy,dict) or not isinstance(frozen.get('parent_policy'),dict):
        raise ValueError('samsung_forward_parent_changed_replan_required')
    if policy==frozen['parent_policy']:return policy
    if not path(root,frozen).is_file():
        raise ValueError('samsung_forward_parent_changed_replan_required')
    value=M._read(path(root,frozen))
    if (not D.valid_hash(value) or value.get('frozen_sha256')!=S.digest(frozen)
        or value.get('old_parent')!=frozen['parent_policy'] or value.get('new_parent')!=policy
        or not D.samsung_equivalent(frozen['parent_policy'],policy)):
        raise ValueError('samsung_forward_parent_changed_replan_required')
    validate(root,frozen,current_kernels(frozen,root))
    return policy


def source_bundle(root,frozen,row):
    """Resolve the capture's P_t, not merely the latest postclose current."""
    from src.engine.scalping import mechanistic_entry_runtime_policy as M
    from src.engine.scalping import entry_setup_evidence as E
    import re
    sha=row.get('bundle_sha256')
    if not re.fullmatch(r'[0-9a-f]{64}',str(sha)):raise ValueError('samsung_capture_bundle_missing')
    bundle=D.validated_generation(Path(root)/'data',sha)
    if bundle['bundle_sha256']!=sha:raise ValueError('samsung_capture_bundle_changed')
    policy=effective_policy(root,frozen,bundle=bundle)
    activation=bundle.get('strategy_activation') or {}
    if not activation or datetime.fromisoformat(row['decision_ts']) < datetime.fromisoformat(activation['effective_from']):
        raise ValueError('samsung_capture_activation_not_proven')
    decision=E.mechanistic_entry_policy_decision(row['setup_evidence'],policy=policy)
    if decision['action']!=row.get('machine_action'):raise ValueError('samsung_actual_action_mismatch')
    return bundle
