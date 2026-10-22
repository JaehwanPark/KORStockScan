"""One-process, read-only code compatibility inside real startup isolation.

The trusted parent authenticates native origin and source-delta proofs before
launch. This child rebinds those proofs to its actual request, kernel boundary,
Git identity and unchanged bytes. It issues no operational handoff or PID claim.
"""
from __future__ import annotations

import ast
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time

SCHEMA = 'main_startup_validation_code_context_v1'
PROOF_SCHEMA = 'main_startup_validation_consumer_code_handoff_v1'
REQUEST_SCHEMA = 'main_policy_load_exit_validation_v1'
ROOT = Path(__file__).resolve().parents[3]
_FAMILIES = {
    'pre_submit_delay': ('pre_submit_delay_handoff', 'policy_sha256'),
    'main_stop': ('main_stop_confirmation_receipt', 'policy_sha256'),
    'holding_vote': ('holding_path_vote_policy_receipt', 'bundle_sha256'),
}
_CONTEXT = None
_MAX_JSON = 8 * 1024 * 1024
# Exact source-only cold preparation repairs. Filled with reviewed Git bytes;
# no AST fallback, runtime authority, or policy resealing is granted here.
REVIEWED_PREPARATION_SOURCES = {'src/engine/scalping/continuous_reversal_policy_v4.py': ('9b1e7ba3fefb6df1c6dc20a0c336f30b006ce982f38764c819a91f5e3f091e4f',
                                                          '85b0611a73c4d7fbbc3b2c2e264a0f7858f78f604f8e58e5face4f760ad4b437'),
 'src/engine/scalping/continuous_reversal_policy_v5.py': ('aad55bc63fbca8ac95d5ec451dea2c741cb857d324959241e5d809b40b7b5278',
                                                          '5f0ce37100b6453c0d143c79007ca45ba77466ffad40f7298a802709c926acb8'),
 'src/engine/scalping/continuous_reversal_policy_v6.py': ('b357d2491d064cf331e8951124fba237043798caacf8da11ed130fb394230d79',
                                                          'eca7f2f2a46d2b4e8f1739e53e6c59d19fd70951c1e2fd786dd8c712201f2460'),
 'src/engine/scalping/entry_machine_source_recovery.py': ('0445f51d0cef807be7639cc41d83581efc015922379c5000fd852b5545f89693',
                                                          '89845a56178c7b2a7322317a5f0c3f9ea2344b0514efc7241d0c5a846acea712'),
 'src/engine/scalping/reversal_anchor_index.py': ('db0c746e27c1f7b914d9250a7336f9fdbb0040756209590e13ff0b309b045dd1',
                                                  '1070133ec9af5500ab139a25f77f2ad9aef3049e9232d341d89188a689a7c37b'),
 'src/engine/scalping/reversal_auxiliary_input_transition.py': ('9e1a206b22e83512eb544201c92b707aca965ef195f8a3698da138a248ccb8cb',
                                                                '07f6af4e43b8fb69a9f1e414d60a4930c7063074f78ffdb0a80789987070cbcb'),
 'src/engine/scalping/reversal_auxiliary_next_session.py': ('c1dffd84447b3b8d5d23eece11d0e48fece8e0467dc439c6f2458ca6fd89b726',
                                                            'c32689f592a5f6558d3404bd9b5495330aefc45715feddf8e579c171d74901c1'),
 'src/engine/scalping/reversal_current_backend.py': ('341b69b19717fa4b994619bb9ea28f76b13362e379f4c494929ad9d4d33ac329',
                                                     'c831b0366ee488eddb9f709ef7811c44cceef58646c1b1e00b2bcc3eb55f4153'),
 'src/engine/scalping/reversal_evaluation_context.py': ('c3d732d937787fd881ebf8f47437f4164ba01582611bc332fe23fd784ed3fc43',
                                                        'b5753ae20f5d8385f7ccf942131d591d5b4feb2dd1f7c278903c74f504201d72'),
 'src/engine/scalping/reversal_extended_runtime.py': ('718b0669d34bf232674c0c2948802c73d2b2bf2a1bdfd2c29c0363a235f19ffc',
                                                      'f6a6b1c7319cf06e29cd08b73f4955e52f4e35f8142978b02999cc47ed976a9b'),
 'src/engine/scalping/reversal_operating_backend.py': ('9ed32405a902a2de68aa9e5e9ed995d81425d6d76e3279c775d60448e57686f8',
                                                       'df60d4ef78cca385b9b7b57a9c82a74efb8d943da6855ac34dd6bf1ebb24b0a6'),
 'src/engine/scalping/reversal_operating_runtime.py': ('06d73bedadc04750c9679e2ff7c1e082e7c889972f5398490da6d0163865bb56',
                                                       '344a03decd050bbd6767e0073c96b8da6384b9ad329e41a70e1ad7f62066533e'),
 'src/engine/scalping/reversal_path_runtime.py': ('476641e53d6c49a0c0c143f11e5a66a59c49d31ab49ee0c4eca7876a65760ced',
                                                  'ffc5e5f6d1f4f50733a7a22d0112c85fdaeaf4b22a319a86f41bd2f89ec5ea36')}
MAIN_PROOF_SCHEMA = 'startup_main_preparation_code_handoff_v1'

# Preserve both the issued preparation and its reviewed same-day stopped carry.
# Evidence: docs/audits/preopen-alert-repair-2026-10-19.md.
REVIEWED_PREPARATION_HISTORY = {
    # Issued native invalidation receipt lineage; source rejection is preserved.
    'src/engine/scalping/entry_machine_source_recovery.py': {
        ('89845a56178c7b2a7322317a5f0c3f9ea2344b0514efc7241d0c5a846acea712',
         'a78c70c5c49169ccb57069df7a524a540a33b615617a49195ddbc343ff9602a5'),
    },
    'src/engine/scalping/reversal_code_handoff.py': {('6c5b8f3013e055ef54774c1e89be66fda93988aa5792e775bb82bac86636cbf0', '16776a22b99bff4054ba99914cd8f7c96e87f6ca9fb1ac041e6a8191723b929d')},
    #0255 source-reader successor: identical cumulative selection over a
    # one-symbol-at-a-time frozen source; require the exact reviewed bytes.
    'src/engine/scalping/reversal_cumulative_postclose.py': {
        ('708ee7428c494f67a7407e5093771f8ddf45ba67227073bea05ff5d87a172493',
         '6adcd6526ca315d53e60d4817cda3cfec1b8ed8db30d624a1c212d6005dbba87'),
    },
    # Reviewed Main SOR eligibility union; exact native signal parity is
    # required separately by the active-policy handoff before any drain.
    'src/trading/market/session_contract.py': {
        ('3a4b68c7d8d613d6ab60e611b5b61f498be0b525b1e35e2bdf3d9d1d396b56a0',
         'dfd0ff3b2a28d8d6581a44762e5b618ae807fdc1c45d7f8cd3128b76be83573c'),
    },
    # Startup log consolidation only; fixed compact model selection is unchanged.
    'src/engine/ai_engine_openai.py': {
        # Source-invalid provenance from the consumed fc51 adapter, no promotion.
        # Local deadline terminals preserve capture/request identity without sending.
        ('3463333df619b52d896ea02779647fa48adf6ae29a45713de80cf31c213806c7',
         '9f9a3561db4dd3247ef14a47e3346f41453c98c0bf42b5ef7ff0be4a2a5b5e56'),
        ('3463333df619b52d896ea02779647fa48adf6ae29a45713de80cf31c213806c7',
         '808000bc7fd3782583a00ecce63e0a5e5704f6e6694e7c3311537aae72579b25'),
        ('194f9dcd748a0c94fe49c12618c3c5eb9f3d81b07de494f0b59ddc349aa43584',
         '703bc5e36bf23a02caf78a3fa8f9251e202979048e4ed1cd64aafed57e732d07'),
        # Issued role-latency successor, already bound by the active handoff.
        ('194f9dcd748a0c94fe49c12618c3c5eb9f3d81b07de494f0b59ddc349aa43584',
         'bdcf09bf1f19e4cb649c01105c7aa363b04bddcb8749793a8f701cc06cc8d185'),
    },
    'src/engine/scalping/ai_decision_trace.py': {
        # Preserve raw failed input without an unperformed quote outcome label.
        ('dfbb14a03971bcfa1f8a0b4c1f3b712d45e7da7fa7259cac125db7f5bb8747a0',
         'ad480ce1fb75ce2ec9217e4623e5de31dfd83e9ff62520934ab0317da60e973b'),
    },
    'src/engine/scalping/reversal_auxiliary_next_session.py': {
        ('c32689f592a5f6558d3404bd9b5495330aefc45715feddf8e579c171d74901c1',
         'eacdffe20114a954e7111026b02ff9c8bdaeb03383e8effa2f78a45a5566e02f'),
        ('c1dffd84447b3b8d5d23eece11d0e48fece8e0467dc439c6f2458ca6fd89b726',
         '301bbe9cc29efa2be9ed9f84b4d919ab1f9adaeae7b2e36ec45a58f3842bdefa'),
        ('301bbe9cc29efa2be9ed9f84b4d919ab1f9adaeae7b2e36ec45a58f3842bdefa',
         'c32689f592a5f6558d3404bd9b5495330aefc45715feddf8e579c171d74901c1'),
    },
}


# Reviewed stopped-origin custody/source recovery; original runtime guards stay unchanged.
REVIEWED_PREPARATION_HISTORY['src/engine/scalping/reversal_code_handoff.py'].update({('ab61f882f4c8bbaddc0576a5765f4f102e38fd824b44a25341ffc78d647741b5', 'c5c6edd558c15bd1067e018d2fa84e4670cd213183baa376cf223e1376ba0238'), ('16776a22b99bff4054ba99914cd8f7c96e87f6ca9fb1ac041e6a8191723b929d', 'c5c6edd558c15bd1067e018d2fa84e4670cd213183baa376cf223e1376ba0238')})

REVIEWED_PREPARATION_HISTORY['src/engine/scalping/reversal_code_handoff.py'].update({('6c5b8f3013e055ef54774c1e89be66fda93988aa5792e775bb82bac86636cbf0', 'b77b63fa5afe9b3dff59266cecce73f92880b5256b12c32343a70aeddba63aa9'), ('c5c6edd558c15bd1067e018d2fa84e4670cd213183baa376cf223e1376ba0238', 'b77b63fa5afe9b3dff59266cecce73f92880b5256b12c32343a70aeddba63aa9'), ('ab61f882f4c8bbaddc0576a5765f4f102e38fd824b44a25341ffc78d647741b5', 'b77b63fa5afe9b3dff59266cecce73f92880b5256b12c32343a70aeddba63aa9'), ('16776a22b99bff4054ba99914cd8f7c96e87f6ca9fb1ac041e6a8191723b929d', 'b77b63fa5afe9b3dff59266cecce73f92880b5256b12c32343a70aeddba63aa9')})


REVIEWED_PREPARATION_HISTORY.setdefault('src/engine/scalping/continuous_reversal_policy_v6.py', set()).update({
    ('b357d2491d064cf331e8951124fba237043798caacf8da11ed130fb394230d79', 'b2be4fe8fe3080bc8e7de9a42c76a8d00985c6ad257a8b1da052fa6a3a108bf2'),
    ('eca7f2f2a46d2b4e8f1739e53e6c59d19fd70951c1e2fd786dd8c712201f2460', 'b2be4fe8fe3080bc8e7de9a42c76a8d00985c6ad257a8b1da052fa6a3a108bf2'),
})

REVIEWED_PREPARATION_HISTORY['src/engine/scalping/reversal_code_handoff.py'].update({
    ('16776a22b99bff4054ba99914cd8f7c96e87f6ca9fb1ac041e6a8191723b929d', '54b9c0efc38700a0cb8722694cdf84b9df8aa478a28f529b2b618f5532559b5a'),
    ('6c5b8f3013e055ef54774c1e89be66fda93988aa5792e775bb82bac86636cbf0', '54b9c0efc38700a0cb8722694cdf84b9df8aa478a28f529b2b618f5532559b5a'),
    ('ab61f882f4c8bbaddc0576a5765f4f102e38fd824b44a25341ffc78d647741b5', '54b9c0efc38700a0cb8722694cdf84b9df8aa478a28f529b2b618f5532559b5a'),
    ('b77b63fa5afe9b3dff59266cecce73f92880b5256b12c32343a70aeddba63aa9', '54b9c0efc38700a0cb8722694cdf84b9df8aa478a28f529b2b618f5532559b5a'),
    ('c5c6edd558c15bd1067e018d2fa84e4670cd213183baa376cf223e1376ba0238', '54b9c0efc38700a0cb8722694cdf84b9df8aa478a28f529b2b618f5532559b5a'),
})

# Reviewed role-based native rollover ancestry for the identical future policy.
REVIEWED_PREPARATION_HISTORY['src/engine/scalping/reversal_code_handoff.py'].update({
    ('ab61f882f4c8bbaddc0576a5765f4f102e38fd824b44a25341ffc78d647741b5', '8681d10376f4228bbe5b9d1d012d3510e8abd89470036077c3c0bc69fad63471'),
    ('b77b63fa5afe9b3dff59266cecce73f92880b5256b12c32343a70aeddba63aa9', '8681d10376f4228bbe5b9d1d012d3510e8abd89470036077c3c0bc69fad63471'),
    ('54b9c0efc38700a0cb8722694cdf84b9df8aa478a28f529b2b618f5532559b5a', '8681d10376f4228bbe5b9d1d012d3510e8abd89470036077c3c0bc69fad63471'),
})

REVIEWED_PREPARATION_HISTORY['deploy/run_threshold_cycle_postclose.sh'] = {('c5e60200a9cf27839204a8fd7d46733f0c10c1a4a0ddeef5bfae35f683b29470', 'dde8ede993e00f022654534a93c9b54c9b38227b9c151bde6288b8782d096067')}

# Reviewed immutable auxiliary snapshots and explicit native active-parent source closure.
REVIEWED_PREPARATION_HISTORY.setdefault('src/engine/scalping/reversal_code_handoff.py', set()).update({('b77b63fa5afe9b3dff59266cecce73f92880b5256b12c32343a70aeddba63aa9', '852d31cba14cfcb68cfb73603de07b30643969c5e476ddca6dde1f2d3a6fc589'), ('54b9c0efc38700a0cb8722694cdf84b9df8aa478a28f529b2b618f5532559b5a', '852d31cba14cfcb68cfb73603de07b30643969c5e476ddca6dde1f2d3a6fc589'), ('8681d10376f4228bbe5b9d1d012d3510e8abd89470036077c3c0bc69fad63471', '852d31cba14cfcb68cfb73603de07b30643969c5e476ddca6dde1f2d3a6fc589')})
REVIEWED_PREPARATION_HISTORY.setdefault('src/engine/scalping/reversal_auxiliary_tuning.py', set()).update({('a8ac3de954b2d6e89e3a46bb49501edc0d35df47621900a1d22b6d8492672412', '0e8f31ed349a6ef17f5f588f8b4bf4180b2f819ab85077a1d51641662611a40a')})

def reviewed_preparation_pair(relative, old, current):
    return (REVIEWED_PREPARATION_SOURCES.get(relative) == (old, current)
            or (old, current) in REVIEWED_PREPARATION_HISTORY.get(relative, ()))


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def _hex(value, length=64):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{' + str(length) + '}', value) is not None


def _read(path, *, maximum=_MAX_JSON):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > maximum:
        raise ValueError('startup_code_context_source_not_regular_bounded')
    with path.open('rb') as stream:
        raw = stream.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError('startup_code_context_source_unbounded')
    return raw


def _json(path):
    value = json.loads(_read(path))
    if not isinstance(value, dict):
        raise ValueError('startup_code_context_object_required')
    return value


def _sha(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('startup_code_context_source_not_regular')
    def identity(value):
        return (value.st_dev, value.st_ino, value.st_mode, value.st_size,
                value.st_mtime_ns, value.st_ctime_ns)
    with path.open('rb') as stream:
        before = identity(os.fstat(stream.fileno()))
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
        if before != identity(os.fstat(stream.fileno())) or path.is_symlink() or before != identity(path.stat()):
            raise ValueError('startup_code_context_source_changed_during_read')
    return digest.hexdigest()


def _check_sources(sources, *, absent_allowed=False):
    if not isinstance(sources, dict) or not sources:
        raise ValueError('startup_code_context_sources_required')
    for name, expected in sources.items():
        if not isinstance(name, str) or not Path(name).is_absolute():
            raise ValueError('startup_code_context_source_path_invalid')
        if expected is None and absent_allowed:
            if Path(name).exists() or Path(name).is_symlink():
                raise ValueError('startup_code_context_absent_source_changed')
        elif not _hex(expected) or _sha(name) != expected:
            raise ValueError('startup_code_context_source_changed')


def _bound_source(sources, path):
    path = Path(path)
    values = {sources[name] for name in (str(path), str(path.resolve(strict=True))) if name in sources}
    if len(values) != 1 or _sha(path) not in values:
        raise ValueError('startup_code_context_source_not_bound')


def _git_head(root):
    """Read Git identity without spawning Git under seccomp."""
    root = Path(root)
    metadata = root / '.git'
    if metadata.is_file():
        line = _read(metadata, maximum=4096).decode().strip()
        if not line.startswith('gitdir: '):
            raise ValueError('startup_code_context_gitdir_invalid')
        directory = (root / line[8:]).resolve(strict=True)
    elif metadata.is_dir() and not metadata.is_symlink():
        directory = metadata
    else:
        raise ValueError('startup_code_context_gitdir_missing')
    head = _read(directory / 'HEAD', maximum=4096).decode().strip()
    if _hex(head, 40):
        return head
    if not head.startswith('ref: '):
        raise ValueError('startup_code_context_git_head_invalid')
    ref = head[5:]
    if not ref.startswith('refs/') or '..' in Path(ref).parts or not re.fullmatch('[A-Za-z0-9._/-]+', ref):
        raise ValueError('startup_code_context_git_ref_invalid')
    common = directory
    if (directory / 'commondir').is_file():
        common = (directory / _read(directory / 'commondir', maximum=4096).decode().strip()).resolve(strict=True)
    for parent in (directory, common):
        if (parent / ref).is_file():
            commit = _read(parent / ref, maximum=4096).decode().strip()
            if _hex(commit, 40):
                return commit
            raise ValueError('startup_code_context_git_ref_invalid')
    packed = common / 'packed-refs'
    if packed.is_file():
        for line in _read(packed).decode().splitlines():
            if line.startswith(('#', '^')):
                continue
            fields = line.split()
            if len(fields) == 2 and fields[1] == ref and _hex(fields[0], 40):
                return fields[0]
    raise ValueError('startup_code_context_git_ref_missing')


def _contract(root, paths, sources):
    if not isinstance(paths, dict) or not paths:
        raise ValueError('startup_code_context_contract_paths_invalid')
    values = {}
    for key, relative in paths.items():
        if (not isinstance(key, str) or not key or not isinstance(relative, str)
                or not relative or Path(relative).is_absolute()):
            raise ValueError('startup_code_context_contract_path_invalid')
        path = Path(root) / relative
        if not path.resolve(strict=True).is_relative_to(root):
            raise ValueError('startup_code_context_contract_path_escape')
        _bound_source(sources, path)
        values[key] = _sha(path)
    return _digest(values)


def _origin(proof, request):
    origin = proof.get('origin')
    if not isinstance(origin, dict):
        raise ValueError('startup_code_context_origin_required')
    sources = origin.get('sources')
    _check_sources(sources)
    if any(proof['source_hashes'].get(name) != sha for name, sha in sources.items()):
        raise ValueError('startup_code_context_origin_not_bound')
    selected = Path(origin.get('selected_release_root') or '')
    commit = origin.get('selected_release_commit')
    if (not selected.is_absolute() or str(selected.resolve(strict=True)) != str(selected)
            or not _hex(commit, 40) or _git_head(selected) != commit
            or not _hex(origin.get('origin_commit'), 40)
            or origin.get('original_code_sha256') != proof['original_code_sha256']):
        raise ValueError('startup_code_context_origin_identity_invalid')
    selected_paths = origin.get('selected_paths', proof['paths'])
    if (not isinstance(selected_paths, dict) or not selected_paths
            or any(proof['paths'].get(key) != name for key, name in selected_paths.items())):
        raise ValueError('startup_code_context_selected_inventory_invalid')
    selected_code = _contract(selected, selected_paths, sources)
    if selected_code != origin.get('selected_runtime_code_sha256'):
        raise ValueError('startup_code_context_selected_contract_changed')
    selector = Path(request['data_root']) / 'runtime/runtime_release_selection.json'
    _bound_source(sources, selector)
    selection = _json(selector)
    if (selection.get('schema') != 'runtime_release_selection_v1'
            or selection.get('release_root') != str(selected) or selection.get('git_commit') != commit):
        raise ValueError('startup_code_context_selected_identity_changed')
    basis = origin.get('basis')
    if basis == 'selected_exact_code_contract':
        if selected_code != proof['original_code_sha256'] or origin['origin_commit'] != commit:
            raise ValueError('startup_code_context_exact_origin_invalid')
    elif basis == 'verified_selected_prepared_code_handoff':
        path = Path(origin.get('code_handoff_receipt_path') or '')
        _bound_source(sources, path)
        receipt = _json(path)
        if (_sha(path) != origin.get('code_handoff_receipt_sha256')
                or receipt.get('schema') != 'prepared_policy_code_handoff_v1'
                or receipt.get('authority') != 'APPROVED_PREPARED_POLICY_PRESERVING_CODE_HANDOFF'
                or receipt.get('receipt_sha256') != _digest({k: v for k, v in receipt.items() if k != 'receipt_sha256'})
                or receipt.get('family') != proof['family'] or receipt.get('target_date') != proof['target_date']
                or receipt.get('policy_sha256') != proof['policy_sha256']
                or receipt.get('original_code_sha256') != proof['original_code_sha256']
                or receipt.get('runtime_code_sha256') != selected_code
                or receipt.get('paths') != selected_paths or receipt.get('release_root') != str(selected)
                or receipt.get('release_commit') != commit or receipt.get('origin_commit') != origin['origin_commit']
                or receipt.get('policy_effect') != 'unchanged'
                or any(receipt.get(k) is not False for k in ('actual_pid_consumed', 'policy_published', 'provider_called', 'broker_called'))):
            raise ValueError('startup_code_context_native_handoff_invalid')
        native_sources = receipt.get('sources')
        _check_sources(native_sources)
        if any(sources.get(name) != sha for name, sha in native_sources.items()):
            raise ValueError('startup_code_context_native_handoff_sources_not_bound')
    elif basis in {'verified_selected_intraday_code_handoff', 'verified_closed_intraday_code_handoff'}:
        if basis == 'verified_closed_intraday_code_handoff':
            closed = origin.get('closed_observation') or {}
            if (closed.get('schema') != 'intraday_closed_consumption_observation_v1'
                    or closed.get('target_date') != proof['target_date']
                    or closed.get('release_commit') != commit
                    or closed.get('pid_identity') != origin.get('pid_identity')
                    or any(closed.get(key) is not False for key in
                           ('runtime_effect','current_observation_verified','new_pid_consumption_claimed'))
                    or not closed.get('source_hashes')
                    or any(sources.get(name) != sha for name,sha in closed['source_hashes'].items())):
                raise ValueError('startup_code_context_closed_origin_invalid')
        handoff_path = Path(origin.get('intraday_handoff_path') or '')
        consumed_path = Path(origin.get('intraday_consumed_path') or '')
        expected = Path(request['data_root'])/'runtime/policy_bootstrap/intraday_handoff'/proof['target_date']
        if (handoff_path != expected/(commit+'.json')
                or consumed_path != expected/(commit+'.consumed.json')):
            raise ValueError('startup_code_context_intraday_path_invalid')
        for path, key in ((handoff_path, 'intraday_handoff_sha256'),
                          (consumed_path, 'intraday_consumed_sha256')):
            _bound_source(sources, path)
            if _sha(path) != origin.get(key):
                raise ValueError('startup_code_context_intraday_source_changed')
        handoff, consumed = _json(handoff_path), _json(consumed_path)
        manifest_path = Path(request['data_root'])/'runtime/policy_bootstrap'/('runtime_policy_bootstrap_'+proof['target_date']+'.json')
        _bound_source(sources, manifest_path)
        live_manifest, prepared_manifest = _json(manifest_path), request['manifest']
        field, _ = _FAMILIES[proof['family']]
        # Prepared and consumed manifests keep distinct generation metadata.
        # Bind both seals and the exact policy/env values this consumer loads.
        if (any(value.get('manifest_sha256') != _digest({k: v for k, v in value.items()
                                                       if k != 'manifest_sha256'})
                for value in (live_manifest, prepared_manifest))
                or live_manifest.get('target_date') != proof['target_date']
                or live_manifest.get(field) != prepared_manifest.get(field)
                or live_manifest.get('env_overrides') != prepared_manifest.get('env_overrides')
                or live_manifest.get('selected_release_sha') != prepared_manifest.get('selected_release_sha')):
            raise ValueError('startup_code_context_intraday_manifest_changed')
        identity = origin.get('pid_identity') or {}
        if (handoff.get('schema') != 'intraday_policy_preserving_release_handoff_v1'
                or handoff.get('authority') != 'APPROVED_INTRADAY_POLICY_PRESERVING_RELEASE_HANDOFF'
                or handoff.get('status') != 'prepared_verified'
                or handoff.get('actual_pid_consumed') is not False
                or handoff.get('policy_effect') != 'unchanged'
                or consumed.get('schema') != 'intraday_policy_preserving_consumption_v1'
                or consumed.get('status') != 'pass' or consumed.get('actual_pid_consumed') is not True
                or consumed.get('handoff_sha256') != origin['intraday_handoff_sha256']
                or consumed.get('pid_identity') != identity or not identity.get('start_ticks')
                or identity.get('cwd') != str(selected/'src')
                or any(row.get('target_date') != proof['target_date']
                       or row.get('selected_release_commit') != commit
                       or row.get('release_root') != str(selected) for row in (handoff, consumed))
                or any(sources.get(name) != sha for name, sha in handoff.get('frozen_files', {}).items())
                or not isinstance(handoff.get('frozen_files'), dict) or not handoff['frozen_files']
                or handoff['frozen_files'].get(str(manifest_path)) != sources[str(manifest_path)]
                or handoff.get('manifest_sha256') != live_manifest['manifest_sha256']
                or not isinstance(identity.get('pid'), int) or identity['pid'] <= 0
                or consumed.get('manifest_sha256') != live_manifest['manifest_sha256']
                or request['manifest'].get('selected_release_sha') != origin['origin_commit']):
            raise ValueError('startup_code_context_intraday_handoff_invalid')
    else:
        raise ValueError('startup_code_context_origin_basis_invalid')


def _proof(proof, family, request):
    if (family not in _FAMILIES or not isinstance(proof, dict)
            or proof.get('schema') != PROOF_SCHEMA or proof.get('status') != 'verified'
            or proof.get('target_date') != request['target_date'] or proof.get('family') != family
            or proof.get('execution_release_root') != request['execution_release_root']
            or proof.get('execution_release_commit') != request['execution_release_commit']
            or proof.get('policy_effect') != 'unchanged'
            or any(proof.get(key, False) is not False for key in ('runtime_effect', 'actual_pid_consumed', 'execution_authority', 'allowed_runtime_apply'))
            or not all(_hex(proof.get(key)) for key in ('policy_sha256', 'original_code_sha256', 'runtime_code_contract_sha256'))):
        raise ValueError('startup_code_context_handoff_invalid')
    field, key = _FAMILIES[family]
    bound = (request.get('manifest') or {}).get(field) or {}
    if bound.get('target_date') != request['target_date'] or bound.get(key) != proof['policy_sha256']:
        raise ValueError('startup_code_context_policy_binding_invalid')
    sources = proof.get('source_hashes')
    _check_sources(sources)
    if any(request['source_hashes'].get(name) != sha for name, sha in sources.items()):
        raise ValueError('startup_code_context_handoff_sources_not_bound')
    if _contract(ROOT, proof.get('paths'), sources) != proof['runtime_code_contract_sha256']:
        raise ValueError('startup_code_context_runtime_contract_changed')
    _origin(proof, request)


def _isolation(request):
    from src.engine.infrastructure.startup_validation_isolation import assert_no_forbidden_attempts
    checked = assert_no_forbidden_attempts()
    capabilities = checked.get('capabilities') or {}
    run = Path(request.get('run_directory') or '')
    if (checked.get('passed') is not True or checked.get('forbidden_attempt_count') != 0
            or not run.is_absolute() or str(run.resolve(strict=True)) != str(run)
            or capabilities.get('schema') != 'main_startup_validation_isolation_v1'
            or capabilities.get('filesystem_write_root') != str(run)
            or capabilities.get('process_group') != os.getpid() or capabilities.get('session_id') != os.getpid()
            or os.getpgrp() != os.getpid() or os.getsid(0) != os.getpid()
            or capabilities.get('landlock_abi', 0) < 3 or capabilities.get('no_new_privileges') is not True
            or any(capabilities.get(key) is not False for key in ('network_access', 'process_creation', 'metadata_changes', 'operational_file_locks'))):
        raise ValueError('startup_code_context_real_isolation_required')
    return run


def install_validation_code_context(request: dict) -> None:
    """Install once, only after the actual mandatory OS boundary is active."""
    global _CONTEXT
    from src.engine.infrastructure.startup_validation_isolation import assert_no_forbidden_attempts
    assert_no_forbidden_attempts()  # Outside isolation leaves the live lookup untouched.
    if _CONTEXT is not None:
        _CONTEXT = {'valid': False}
        raise ValueError('startup_code_context_already_installed')
    _CONTEXT = {'valid': False}
    run = _isolation(request)
    request = json.loads(json.dumps(request, allow_nan=False))
    if (request.get('schema') != REQUEST_SCHEMA or not _hex(request.get('run_id'), 32)
            or run.name != request['run_id'] or request.get('execution_release_root') != str(ROOT)
            or not _hex(request.get('execution_release_commit'), 40)
            or _git_head(ROOT) != request['execution_release_commit']
            or date.fromisoformat(request['target_date']).isoformat() != request['target_date']
            or request.get('request_sha256') != _digest({k: v for k, v in request.items() if k != 'request_sha256'})
            or any(request.get(key, False) is not False for key in ('runtime_effect', 'actual_pid_consumed', 'allowed_runtime_apply'))):
        raise ValueError('startup_code_context_request_invalid')
    request_path = run / 'request.json'
    if _json(request_path) != request:
        raise ValueError('startup_code_context_request_file_changed')
    sources = request.get('source_hashes')
    _check_sources(sources, absent_allowed=True)
    _bound_source(sources, Path(__file__))
    proofs = request.get('candidate_code_handoffs')
    if not isinstance(proofs, dict) or not proofs:
        raise ValueError('startup_code_context_handoffs_required')
    for family, proof in proofs.items():
        _proof(proof, family, request)
    if request.get('main_preparation_code_handoff') is not None:
        _main_proof(request['main_preparation_code_handoff'], request)
    _isolation(request)
    _CONTEXT = dict(valid=True, pid=os.getpid(), start_ticks=_read('/proc/self/stat', maximum=65536).decode().rsplit(')', 1)[1].split()[19],
                    request=request, request_path=str(request_path), request_sha256=_sha(request_path))
    _CONTEXT['request_identity'] = _request_identity(request_path)
    if request.get('main_preparation_code_handoff') is not None:
        proof = request['main_preparation_code_handoff']
        mounts = _sha('/proc/self/mountinfo')
        _CONTEXT['main_anchor_identities'] = {path: _request_identity(path)
            for path in proof['source_hashes']}
        if _sha('/proc/self/mountinfo') != mounts:
            _CONTEXT = {'valid': False}
            raise ValueError('startup_main_mount_generation_changed')
        _CONTEXT['main_mountinfo_sha256'] = mounts
        _CONTEXT['delegation'] = dict(digest_reused_reads=0, digest_reused_bytes=0, auxiliary_manifests=[])
        from src.engine.infrastructure.validation_digest_session import ACTIVE
        if ACTIVE.get() is not None:
            _CONTEXT = {'valid': False}
            raise ValueError('startup_code_context_digest_owner_already_active')
        ACTIVE.set(_PreparationDigests())


def verify_validation_consumer_code(day, *, family, policy_sha, expected, paths, actual):
    """Return None outside this context; never soften the ordinary live guard."""
    global _CONTEXT
    if _CONTEXT is None:
        return None
    context = _CONTEXT
    try:
        if context.get('valid') is not True:
            raise ValueError('startup_code_context_invalid')
        request = context['request']
        _isolation(request)
        if (os.getpid() != context['pid'] or _git_head(ROOT) != request['execution_release_commit']
                or _read('/proc/self/stat', maximum=65536).decode().rsplit(')', 1)[1].split()[19] != context['start_ticks']
                or _sha(context['request_path']) != context['request_sha256']
                or _json(context['request_path']) != request):
            raise ValueError('startup_code_context_execution_changed')
        proof = request['candidate_code_handoffs'].get(family)
        if (not isinstance(proof, dict) or day != request['target_date']
                or policy_sha != proof['policy_sha256'] or expected != proof['original_code_sha256']
                or actual != proof['runtime_code_contract_sha256'] or paths != proof['paths']):
            raise ValueError('startup_code_context_consumer_binding_invalid')
        _check_sources(request['source_hashes'], absent_allowed=True)
        _proof(proof, family, request)
        return dict(status='verified_intraday_consumer_repair', verification_basis=SCHEMA,
            basis=SCHEMA, target_date=day, policy_sha256=policy_sha,
            code_contract_sha256=expected, runtime_code_contract_sha256=actual,
            origin_commit=proof['origin']['origin_commit'], policy_effect='unchanged',
            actual_pid_consumed=False, execution_authority=False)
    except (OSError, ValueError, TypeError, KeyError):
        _CONTEXT = {'valid': False}
        raise


def _main_inventories(bundle):
    result = []
    seen = set()
    while bundle:
        family = bundle.get('continuous_reversal') or {}
        ident = bundle.get('bundle_sha256')
        if ident in seen or len(result) >= 4 or not _hex(ident):
            raise ValueError('startup_main_inventory_cycle_or_identity')
        seen.add(ident)
        expected = family.get('contract_file_sha256')
        if (family.get('schema') not in {'continuous_reversal_policy_v4',
                'continuous_reversal_policy_v5', 'continuous_reversal_policy_v6'}
                or not isinstance(expected, dict) or not expected
                or not all(isinstance(k, str) and Path(k).name == k and _hex(v)
                           for k, v in expected.items())):
            raise ValueError('startup_main_inventory_invalid')
        result.append(dict(bundle_sha256=ident, target_date=bundle['target_date'],
            family_sha256=family['family_sha256'], schema=family['schema'], expected=expected,
            origin_commit=family['release_commit']))
        bundle = family.get('native_parent_bundle')
    return result


def _code_path(name):
    if name == 'session_contract.py':
        return 'src/trading/market/' + name
    if name == 'ai_engine_openai.py':
        return 'src/engine/' + name
    if not isinstance(name, str) or Path(name).name != name or not name.endswith('.py'):
        raise ValueError('startup_main_code_name_invalid')
    return 'src/engine/scalping/' + name


def _pairs(expected, actual):
    if not isinstance(expected, dict) or not expected or set(expected) != set(actual):
        raise ValueError('startup_main_code_inventory_changed')
    for relative, old in expected.items():
        current = actual[relative]
        if not _hex(old) or not _hex(current):
            raise ValueError('startup_main_code_digest_invalid')
        if old != current and not reviewed_preparation_pair(relative, old, current):
            raise ValueError('startup_main_code_pair_unreviewed:' + relative)


def _historical_code_refs(manifest):
    root = Path(manifest['frozen_validator_root'])
    refs = {}
    for name, expected in manifest['semantic_code_hashes'].items():
        relative = _code_path(name)
        path = root / relative
        if path.resolve(strict=True) != path or _sha(path) != expected:
            raise ValueError('startup_main_historical_code_changed')
        refs[relative] = dict(path=str(path), sha256=expected)
    return refs


_DELAY_CONTRACT_OWNER = 'src/engine/scalping/pre_submit_delay_initial_policy.py'


def _delay_contract_paths(raw):
    """Read the immutable origin declaration without importing its module."""
    declarations = [node.value for node in ast.parse(raw).body if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == 'CONTRACT_PATHS' for target in node.targets)]
    if len(declarations) != 1 or not isinstance(declarations[0], ast.Tuple):
        raise ValueError('startup_delay_native_contract_declaration_invalid')
    paths = ast.literal_eval(declarations[0])
    if (not 1 <= len(paths) <= 128 or any(not isinstance(path, str)
            or not path.startswith('src/') or not path.endswith('.py')
            or str(Path(path)) != path or '..' in Path(path).parts for path in paths)
            or len(set(paths)) != len(paths) or _DELAY_CONTRACT_OWNER not in paths):
        raise ValueError('startup_delay_native_contract_declaration_invalid')
    return list(paths)


def _native_verifier_code(proof):
    """Keep actual native verifier code distinct from consumed policy origin."""
    native=proof['native_verification']
    root=native.get('verification_code_root',proof['selected_release_root'])
    commit=native.get('verification_code_commit',proof['selected_release_commit'])
    allowed={(proof['selected_release_root'],proof['selected_release_commit']),
             (proof['execution_release_root'],proof['execution_release_commit'])}
    if (root,commit) not in allowed or Path(root).resolve(strict=True)!=Path(root):
        raise ValueError('startup_native_verifier_code_identity_invalid')
    return Path(root),commit


def _attest_delay_inventory(selected, commit, records, sources):
    """Parent-only exact Git origin; the child consumes no Git subprocess."""
    import subprocess
    if not records:
        return None
    selected = Path(selected)
    if (selected.resolve(strict=True) != selected or not _hex(commit, 40)
            or _git_head(selected) != commit):
        raise ValueError('startup_delay_native_inventory_origin_changed')
    raw = subprocess.check_output(['git', '-C', str(selected), 'show', commit + ':' + _DELAY_CONTRACT_OWNER])
    paths = _delay_contract_paths(raw)
    inventory = {}
    for relative in paths:
        path = selected / relative
        original = raw if relative == _DELAY_CONTRACT_OWNER else subprocess.check_output(
            ['git', '-C', str(selected), 'show', commit + ':' + relative])
        expected = hashlib.sha256(original).hexdigest()
        if path.resolve(strict=True) != path or _sha(path) != expected:
            raise ValueError('startup_delay_native_code_git_changed')
        if sources.setdefault(str(path), expected) != expected:
            raise ValueError('startup_delay_native_source_conflict')
        inventory[relative] = expected
    if any(item.get('native_code_inventory') != inventory for item in records.values()):
        raise ValueError('startup_delay_native_code_inventory_invalid')
    return dict(schema='startup_delay_native_inventory_git_v1', origin_commit=commit,
        selected_release_root=str(selected), declaration_path=str(selected/_DELAY_CONTRACT_OWNER),
        declaration_sha256=inventory[_DELAY_CONTRACT_OWNER], contract_paths=paths, code_hashes=inventory)


def _native_main_basis(native):
    """Keep PREOPEN custody scope distinct from this invocation's Main closure."""
    if native.get('status') != 'pass' or native.get('findings'):
        return None
    if native.get('validation_scope') == 'current_full_contract':
        return 'same_invocation_selected_native_full_verification'
    consumed = native.get('native_predecessor_consumption') or {}
    if (native.get('validation_scope') == 'intraday_preserved_historical_generation'
            and native.get('handoff_basis') == 'native_consumed_preopen_preserved_generation'
            and consumed.get('schema') == 'intraday_pid_consumption_verification_v1'
            and consumed.get('status') == 'pass' and consumed.get('findings') == []
            and consumed.get('basis') == 'native_preopen'
            and consumed.get('actual_pid_consumed') is True
            and consumed.get('target_date') == native.get('target_date')
            and consumed.get('selected_release_commit') == native.get('preserved_preopen_commit')
            and _hex(consumed.get('manifest_sha256'))):
        return 'same_invocation_selected_consumed_preopen_native_validation'
    if (native.get('validation_scope') == 'intraday_preserved_historical_generation'
            and native.get('handoff_basis') in {'intraday_preserved_preopen_generation',
                'intraday_preserved_preopen_generation_current_postclose_resealed'}
            and _hex(native.get('preserved_preopen_commit'), 40)):
        return ('same_invocation_selected_prepared_intraday_native_validation'
                if native.get('prepared_intraday_handoff')
                else 'same_invocation_selected_intraday_native_validation')
    return None


def _preserved_native_sources(proof):
    """Same-invocation full bootstrap with prepared or consumed source custody.

    Intraday Main can preserve a prepared policy without publishing an auxiliary
    transition manifest. That path must supply its own nonempty native closure;
    an empty auxiliary manifest set alone never authorizes delegation.
    """
    native=proof['native_verification'];closure=proof['closure']
    records=closure.get('preserved_generations')
    if not records:
        return {}
    native_consumed = (_native_main_basis(native) ==
        'same_invocation_selected_consumed_preopen_native_validation')
    native_prepared = (_native_main_basis(native) ==
        'same_invocation_selected_prepared_intraday_native_validation')
    prepared_commit = (native.get('preserved_preopen_commit') if native_prepared
                       else proof['selected_release_commit'])
    if native.get('validation_scope')=='current_full_contract' or native_consumed or native_prepared:
        if not isinstance(records,dict) or len(records)!=1:
            raise ValueError('startup_prepared_native_scope_invalid')
        data=Path(proof['policy_path']).parents[3];day=proof['target_date']
        index=data/'runtime/policy_bootstrap/prepared'/day/'latest.json'
        view=_json(index);prepared=Path(view['receipt_path']);sha=_sha(prepared)
        record=records.get(sha);value=_json(prepared)
        if (prepared.resolve().parent.parent!=index.parent.resolve()
                or view.get('schema')!='next_preopen_readiness_index_v1'
                or view.get('target_date')!=day or view.get('receipt_sha256')!=sha
                or not isinstance(record,dict)
                or record.get('schema')!='startup_native_prepared_preopen_closure_v1'
                or record.get('prepared_receipt_path')!=str(prepared)
                or record.get('target_date')!=day or value.get('target_date')!=day
                or value.get('schema')!='next_preopen_readiness_v1'
                or value.get('status')!='prepared_verified'
                or value.get('runtime_effect') is not False or value.get('actual_pid_consumed') is not False
                or value.get('source_date')!=native.get('source_date')
                or value.get('selected_release_commit')!=prepared_commit
                or record.get('selected_release_commit')!=prepared_commit
                or (value.get('activation_candidate') or {}).get('bundle_sha256')!=proof['policy_sha256']):
            raise ValueError('startup_prepared_native_identity_invalid')
        refs={str(prepared):sha}
        for name,digest in (('manifest_path','manifest_file_sha256'),('env_path','env_sha256'),
                ('verification_path','verification_sha256'),('controller_path','controller_sha256'),
                ('summary_path','summary_sha256')):
            refs[value[name]]=value[digest]
        for source in value.get('policy_receipts',[]):refs[source['path']]=source['sha256']
        if refs!=record.get('sources'):
            raise ValueError('startup_prepared_native_source_set_changed')
        _check_sources(refs)
        full=record.get('full_bootstrap') or {};checked=full.get('result') or {}
        manifest=_json(Path(value['manifest_path']))
        if (full.get('path')!=value['manifest_path'] or full.get('sha256')!=value['manifest_file_sha256']
                or full.get('write') is not False or full.get('full_native_verification') is not True
                or checked.get('status')!='pass' or checked.get('findings')
                or checked.get('target_date')!=day
                or not _hex(value.get('manifest_content_sha256'))
                or checked.get('manifest_sha256')!=value['manifest_content_sha256']
                or record.get('prepared_manifest_sha256')!=value['manifest_content_sha256']
                or manifest.get('manifest_sha256')!=value['manifest_content_sha256']
                or manifest.get('target_date')!=day
                or manifest.get('selected_release_sha')!=prepared_commit):
            raise ValueError('startup_prepared_full_bootstrap_unbound')
        refs[str(index)]=_sha(index)
        if native_prepared:
            binding = native['prepared_intraday_handoff']
            observation = native.get('stopped_preparation_observation')
            if observation is not None:
                if (observation.get('target_date') != day
                        or observation.get('release_commit') != proof['selected_release_commit']
                        or any(observation.get(k) is not False for k in
                               ('runtime_effect','actual_pid_consumed','allowed_runtime_apply'))
                        or not observation.get('source_hashes')
                        or any(binding['sources'].get(name) != sha
                               for name, sha in observation['source_hashes'].items())):
                    raise ValueError('startup_stopped_preparation_observation_invalid')
                _check_sources(observation['source_hashes'])

            path = data/'runtime/policy_bootstrap/intraday_handoff'/day/(proof['selected_release_commit']+'.json')
            handoff = _json(path)
            expected_sources = {**handoff.get('frozen_files', {}), str(path): _sha(path),
                **((observation or {}).get('source_hashes') or {})}
            if observation is not None and observation.get('original_first_launch_before') != handoff.get('first_launch_before'):
                raise ValueError('startup_stopped_preparation_expiry_changed')
            selected = _json(data/'runtime/runtime_release_selection.json')
            active = data/'runtime/policy_bootstrap'/('runtime_policy_bootstrap_'+day+'.json')
            active_body = _json(active)
            if (binding.get('path') != str(path) or binding.get('sha256') != _sha(path)
                    or binding.get('sources') != expected_sources or binding.get('full_native_validation') is not True
                    or native.get('actual_pid_consumed') is not False
                    or handoff.get('schema') != 'intraday_policy_preserving_release_handoff_v1'
                    or handoff.get('authority') != 'APPROVED_INTRADAY_POLICY_PRESERVING_RELEASE_HANDOFF'
                    or handoff.get('status') != 'prepared_verified' or handoff.get('target_date') != day
                    or handoff.get('selected_release_commit') != proof['selected_release_commit']
                    or handoff.get('release_root') != proof['selected_release_root']
                    or handoff.get('actual_pid_consumed') is not False or handoff.get('policy_effect') != 'unchanged'
                    or handoff.get('prepared_receipt_path') != str(prepared)
                    or handoff.get('prepared_receipt_sha256') != sha
                    or handoff.get('manifest_sha256') != active_body.get('manifest_sha256')
                    or active_body.get('target_date') != day
                    or expected_sources.get(str(active)) != _sha(active)
                    or selected.get('git_commit') != proof['selected_release_commit']
                    or selected.get('release_root') != proof['selected_release_root']
                    or selected.get('actual_pid_consumed') is not False):
                raise ValueError('startup_prepared_intraday_handoff_invalid')
            _check_sources(expected_sources)
            refs.update(expected_sources)
            refs[str(data/'runtime/runtime_release_selection.json')] = _sha(data/'runtime/runtime_release_selection.json')
        if native_consumed:
            consumed=native['native_predecessor_consumption']
            selection=data/'runtime/runtime_release_selection.json';selected=_json(selection)
            actor=selected.get('actual_pid_receipt') or {}
            identity=dict(pid=actor.get('pid'),start_ticks=str(actor.get('start_ticks')),
                          cwd=actor.get('process_cwd'))
            if (selected.get('schema')!='runtime_release_selection_v1'
                    or selected.get('actual_pid_consumed') is not True
                    or selected.get('release_root')!=proof['selected_release_root']
                    or selected.get('git_commit')!=proof['selected_release_commit']
                    or consumed.get('release_root')!=proof['selected_release_root']
                    or consumed.get('pid_identity')!=identity
                    or type(identity['pid']) is not int or identity['pid']<=0
                    or identity['cwd']!=str(Path(proof['selected_release_root'])/'src')):
                raise ValueError('startup_native_consumption_identity_invalid')
            active=data/'runtime/policy_bootstrap'/('runtime_policy_bootstrap_'+day+'.json')
            env=active.with_suffix('.env')
            if _json(active).get('manifest_sha256')!=consumed['manifest_sha256']:
                raise ValueError('startup_native_consumption_bootstrap_changed')
            refs.update({str(p):_sha(p) for p in (selection,active,env)})
        return refs
    if (native.get('validation_scope')!='intraday_preserved_historical_generation'
            or _native_main_basis(native)!='same_invocation_selected_intraday_native_validation'
            or not isinstance(records,dict) or len(records) not in {1,2}):
        raise ValueError('startup_preserved_native_scope_invalid')
    data=Path(proof['policy_path']).parents[3];day=proof['target_date']
    commit=proof['selected_release_commit'];selected=proof['selected_release_root']
    base=data/'runtime/policy_bootstrap/intraday_handoff'/day
    path=base/(commit+'.json');consumed=base/(commit+'.consumed.json')
    sha=_sha(path);record=records.get(sha)
    if (not isinstance(record,dict)
            or record.get('schema')!='startup_native_preserved_preopen_closure_v1'
            or record.get('target_date')!=day or record.get('selected_release_commit')!=commit
            or record.get('handoff_path')!=str(path) or record.get('consumed_path')!=str(consumed)):
        raise ValueError('startup_preserved_native_identity_invalid')
    handoff=_json(path);receipt=_json(consumed)
    manifest_sha=record.get('manifest_sha256')
    if (handoff.get('schema')!='intraday_policy_preserving_release_handoff_v1'
            or handoff.get('status')!='prepared_verified'
            or handoff.get('target_date')!=day or handoff.get('selected_release_commit')!=commit
            or handoff.get('release_root')!=selected or handoff.get('actual_pid_consumed') is not False
            or handoff.get('manifest_sha256')!=manifest_sha
            or receipt.get('schema')!='intraday_policy_preserving_consumption_v1'
            or receipt.get('status')!='pass' or receipt.get('actual_pid_consumed') is not True
            or receipt.get('handoff_sha256')!=sha or receipt.get('manifest_sha256')!=manifest_sha
            or receipt.get('target_date')!=day or receipt.get('selected_release_commit')!=commit
            or receipt.get('release_root')!=selected or not receipt.get('pid_identity')):
        raise ValueError('startup_preserved_native_consumption_invalid')
    refs={**handoff['frozen_files'],str(path):sha,str(consumed):_sha(consumed)}
    if refs!=record.get('sources'):
        raise ValueError('startup_preserved_native_source_set_changed')
    _check_sources(refs)
    prepared=Path(handoff['prepared_receipt_path']);value=_json(prepared)
    full=record.get('full_bootstrap') or {};checked=full.get('result') or {}
    bootstrap=prepared.parent/('runtime_policy_bootstrap_'+day+'.json')
    if (refs.get(str(prepared))!=handoff.get('prepared_receipt_sha256')
            or value.get('source_date')!=native.get('source_date') or value.get('target_date')!=day
            or value.get('status')!='prepared_verified'
            or (value.get('activation_candidate') or {}).get('bundle_sha256')!=proof['policy_sha256']
            or full.get('path')!=str(bootstrap) or _sha(bootstrap)!=full.get('sha256')
            or full.get('write') is not False or full.get('full_native_verification') is not True
            or checked.get('status')!='pass' or checked.get('findings')
            or checked.get('target_date')!=day
            or record.get('prepared_manifest_sha256')!=value.get('manifest_content_sha256')
            or not _hex(value.get('manifest_content_sha256'))
            or checked.get('manifest_sha256')!=value['manifest_content_sha256']
            or _json(bootstrap).get('manifest_sha256')!=value['manifest_content_sha256']):
        raise ValueError('startup_preserved_full_bootstrap_unbound')
    refs[str(bootstrap)]=full['sha256']
    if len(records)==2:
        # A full native handoff can also visit its original prepared generation.
        # Admit only that exact ancestor and recheck its complete native contract.
        prepared_sha=handoff['prepared_receipt_sha256']
        ancestor=records.get(prepared_sha)
        if (set(records)!={sha,prepared_sha} or not isinstance(ancestor,dict)
                or ancestor.get('prepared_receipt_path')!=str(prepared)
                or ancestor.get('full_bootstrap')!=full):
            raise ValueError('startup_preserved_native_ancestry_invalid')
        ancestor_refs=_preserved_native_sources(dict(proof,
            selected_release_commit=value.get('selected_release_commit'),
            native_verification=dict(native,validation_scope='current_full_contract'),
            closure=dict(closure,preserved_generations={prepared_sha:ancestor})))
        if any(path in refs and refs[path]!=digest for path,digest in ancestor_refs.items()):
            raise ValueError('startup_preserved_native_ancestry_source_changed')
        refs.update(ancestor_refs)
    return refs


def bind_main_preparation(root, commit, data_root, intake):
    """Parent-only Git attestation after this invocation's full native verify."""
    import subprocess
    root = Path(root).resolve(strict=True)
    data_root = Path(data_root).resolve(strict=True)
    selected = Path(intake['selected_root']).resolve(strict=True)
    original_commit = intake['selected_commit']
    native = intake['native_verification']
    closure = native.get('native_machine_closure')
    day = intake['manifest']['target_date']
    if (_native_main_basis(native) == 'same_invocation_selected_intraday_native_validation'
            and native.get('actual_pid_consumed') is False):
        from src.engine.automation import intraday_release_handoff as H
        path, consumed = H._paths(day, original_commit)
        if not consumed.exists():
            observation = native.get('stopped_preparation_observation')
            if observation is not None:
                with H.stopped_preparation_review(day) as current:
                    if current != observation:
                        raise ValueError('startup_stopped_preparation_proof_changed')
                    checked = H._verify_handoff(day, original_commit)
            else:
                checked = H._verify_handoff(day, original_commit)
            if checked.get('status') != 'pass':
                raise ValueError('startup_prepared_intraday_native_validation_failed')
            handoff = checked['handoff']
            native = dict(native, prepared_intraday_handoff=dict(path=str(path), sha256=_sha(path),
                sources={**handoff['frozen_files'], str(path): _sha(path),
                    **((native.get('stopped_preparation_observation') or {}).get('source_hashes') or {})},
                full_native_validation=True))
    if (native.get('status') != 'pass' or native.get('findings')
            or _native_main_basis(native) is None
            or native.get('target_date') != day or native.get('selected_release_commit') != original_commit
            or (native.get('validation_scope') == 'intraday_preserved_historical_generation'
                and native.get('preserved_preopen_commit') != intake['manifest'].get('selected_release_sha'))
            or not isinstance(closure, dict)):
        raise ValueError('startup_main_native_full_validation_required')
    policy = data_root / 'runtime/mechanistic_entry_policy/candidates' / ('policy_' + day + '.json')
    bundle = _json(policy)
    if (bundle.get('bundle_sha256') != intake['receipt']['activation_candidate']['bundle_sha256']
            or bundle['bundle_sha256'] not in closure.get('bundles', {})):
        raise ValueError('startup_main_native_bundle_unobserved')
    inventories = _main_inventories(bundle)
    expected = {}
    inventory_attestations = {}
    for item in inventories:
        if not _hex(item['origin_commit'], 40):
            raise ValueError('startup_main_inventory_origin_invalid')
        verified = {}
        for name, value in item['expected'].items():
            relative = _code_path(name)
            original = hashlib.sha256(subprocess.check_output(['git', '-C', str(selected),
                'show', item['origin_commit'] + ':' + relative])).hexdigest()
            if original != value:
                raise ValueError('startup_main_inventory_git_origin_changed')
            verified[relative] = original
            expected[relative] = _sha(selected / relative)
        inventory_attestations[item['bundle_sha256']] = dict(origin_commit=item['origin_commit'],
            code_hashes=verified)
    manifests = closure.get('manifests')
    preserved_sources=_preserved_native_sources(dict(policy_path=str(policy),policy_sha256=bundle['bundle_sha256'],
        target_date=day,selected_release_commit=original_commit,selected_release_root=str(selected),
        native_verification=native,closure=closure))
    if not isinstance(manifests, dict) or len(manifests)>16 or not (manifests or preserved_sources):
        raise ValueError('startup_main_manifest_closure_required')
    sources = {str(policy): _sha(policy),
        str(data_root / 'runtime/runtime_release_selection.json'): _sha(data_root / 'runtime/runtime_release_selection.json')}
    sources.update(preserved_sources)
    histories, native_readers = {}, {}
    for ident, observed in manifests.items():
        manifest = _json(observed['path'])
        if (manifest.get('artifact_content_sha256') != ident or _sha(observed['path']) != observed['sha256']
                or observed['bundle_sha256'] != bundle['bundle_sha256'] or observed['target_date'] != day):
            raise ValueError('startup_main_manifest_closure_changed')
        sources[observed['path']] = observed['sha256']
        declared = {ref['path'] for ref in manifest['sources']}
        declared.update(manifest['ledger_pack_paths']); declared.update(manifest['baseline_dependency_paths'])
        dependencies = observed.get('dependencies')
        if not isinstance(dependencies, list) or len(dependencies) > 8192:
            raise ValueError('startup_main_manifest_dependency_set_changed')
        for dependency, _ in dependencies:
            path = Path(dependency)
            if dependency in declared:
                continue
            if not path.is_relative_to(selected/'src') or path.resolve(strict=True) != path or path.suffix != '.py':
                raise ValueError('startup_main_native_reader_path_invalid')
            relative = str(path.relative_to(selected))
            digest = hashlib.sha256(subprocess.check_output(
                ['git', '-C', str(selected), 'show', original_commit+':'+relative])).hexdigest()
            if _sha(path) != digest or len(native_readers) >= 128 and relative not in native_readers:
                raise ValueError('startup_main_native_reader_git_changed')
            native_readers[relative] = digest
            sources[str(path)] = digest
        histories[ident] = _historical_code_refs(manifest)
        for relative, ref in histories[ident].items():
            sources[ref['path']] = ref['sha256']
            selected_hash = _sha(selected / relative)
            if expected.setdefault(relative, selected_hash) != selected_hash:
                raise ValueError('startup_main_origin_inventory_conflict')
        for field in ('next_session_code_hashes', 'reader_code_hashes'):
            for name, value in manifest[field].items():
                relative = _code_path(name)
                selected_hash = _sha(selected / relative)
                if (value != selected_hash and not reviewed_preparation_pair(relative, value, selected_hash)
                        or expected.setdefault(relative, selected_hash) != selected_hash):
                    raise ValueError('startup_main_origin_inventory_conflict:' + relative)
    # These entry/configuration owners are not all in the historical inventory.
    # Bind their exact original/current bytes without adding retroactive keys.
    for relative in REVIEWED_PREPARATION_SOURCES:
        old = hashlib.sha256(subprocess.check_output(
            ['git', '-C', str(selected), 'show', original_commit + ':' + relative])).hexdigest()
        if expected.setdefault(relative, old) != old:
            raise ValueError('startup_main_origin_inventory_conflict')
    actual = {}
    for relative, old in expected.items():
        for checkout, revision, digest in ((selected, original_commit, old), (root, commit, None)):
            path = checkout / relative
            if path.resolve(strict=True) != path or path.is_symlink():
                raise ValueError('startup_main_source_alias')
            value = _sha(path)
            git_value = hashlib.sha256(subprocess.check_output(
                ['git', '-C', str(checkout), 'show', revision + ':' + relative])).hexdigest()
            if value != git_value or (digest is not None and value != digest):
                raise ValueError('startup_main_source_git_or_origin_changed')
            sources[str(path)] = value
            if checkout == root:
                actual[relative] = value
    _pairs(expected, actual)
    for item in inventories:
        values = {_code_path(name): value for name, value in item['expected'].items()}
        _pairs(values, {name: actual[name] for name in values})
    for refs in histories.values():
        _pairs({name: ref['sha256'] for name, ref in refs.items()},
               {name: actual[name] for name in refs})
    # A delay rebuild is observed in this same native verification process.
    # Bind its actual immutable documents and selected implementation bytes to
    # the request/source CAS; this grants no standalone selection authority.
    for item in closure.get('delay_selections', {}).values():
        for ref in item['artifacts'].values():
            if sources.setdefault(ref['path'], ref['sha256']) != ref['sha256']:
                raise ValueError('startup_delay_native_source_conflict')
    native_root,native_commit=_native_verifier_code(dict(native_verification=native,
        selected_release_root=str(selected),selected_release_commit=original_commit,
        execution_release_root=str(root),execution_release_commit=commit))
    delay_inventory = _attest_delay_inventory(native_root, native_commit,
        closure.get('delay_selections', {}), sources)
    proof = dict(schema=MAIN_PROOF_SCHEMA, target_date=day, policy_path=str(policy),
        policy_sha256=bundle['bundle_sha256'], policy_file_sha256=_sha(policy),
        execution_release_root=str(root), execution_release_commit=commit,
        selected_release_root=str(selected), selected_release_commit=original_commit,
        original_code_hashes=expected, runtime_code_hashes=actual, inventories=inventories,
        inventory_git_attestations=inventory_attestations,
        delay_inventory_git_attestation=delay_inventory,
        historical_semantic_code_sources=histories, native_reader_code_sources=native_readers,
        source_hashes=sources, closure=closure,
        native_verification={k: v for k, v in native.items() if k != 'native_machine_closure'},
        delegation_basis=_native_main_basis(native),
        policy_effect='unchanged', runtime_effect=False, allowed_runtime_apply=False,
        actual_pid_consumed=False)
    _check_native_closure(proof)
    return proof


def _check_native_closure(proof):
    """Check generations, not a cached verdict, for delegated process-only work."""
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.infrastructure.validation_digest_session import identity
    closure = proof['closure']
    native = proof['native_verification']
    binding = closure.get('digest_binding') or {}
    data_root = Path(proof['policy_path']).parents[3]
    io = native.get('native_validation_io') or {}
    if (closure.get('schema') != 'startup_native_machine_closure_v1' or not _hex(closure.get('run_id'), 32)
            or native.get('status') != 'pass' or native.get('findings')
            or _native_main_basis(native) is None
            or native.get('target_date') != proof['target_date']
            or native.get('selected_release_commit') != proof['selected_release_commit']
            or binding.get('role') != 'postclose' or binding.get('day') != native.get('source_date')
            or binding.get('lexical_root') != str(data_root)
            or binding.get('resolved_root') != str(data_root.resolve(strict=True))
            or binding.get('pid') != (io.get('stats') or {}).get('pid')
            or io.get('remaining_entries') != 0
            or binding.get('boot_id') != _read('/proc/sys/kernel/random/boot_id', maximum=128).decode().strip()):
        raise ValueError('startup_main_native_closure_invalid')
    bundles = closure.get('bundles')
    bundle = _json(proof['policy_path'])
    if (not isinstance(bundles, dict) or not 1 <= len(bundles) <= 16
            or bundles.get(proof['policy_sha256']) != dict(target_date=proof['target_date'],
                family_sha256=bundle['continuous_reversal']['family_sha256'])):
        raise ValueError('startup_main_native_bundle_unobserved')
    _delay_selection_records(proof)
    entries = closure.get('digest_entries')
    if (not isinstance(entries, dict) or len(entries) > 4096
            or len(json.dumps(entries, sort_keys=True, separators=(',', ':')).encode()) > 512 * 1024):
        raise ValueError('startup_main_digest_closure_unbounded')
    for path, entry in entries.items():
        if (not isinstance(entry, dict) or set(entry) not in ({'identity', 'digest', 'created'},
                {'identity','digest','created','native_generation_proof'})
                or 'native_generation_proof' in entry and not _hex(entry['native_generation_proof'])
                or not _hex(entry.get('digest'))
                or identity(path) != entry.get('identity')
                or entry['identity'][4] < 1024 * 1024
                or entry['identity'][2] != Path(binding['resolved_root']).stat().st_dev
                or entry['identity'][8] != os.getuid()
                or type(entry['created']) not in (int, float) or not 0 <= time.time() - entry['created'] <= 600
                or not Path(path).resolve().is_relative_to(binding['resolved_root'])):
            raise ValueError('startup_main_digest_generation_changed')
    sessions=closure.get('digest_sessions')
    if sessions is not None:
        if not isinstance(sessions,dict) or not 1<=len(sessions)<=8:
            raise ValueError('startup_main_digest_session_set_invalid')
        for key,observed in sessions.items():
            owner=observed.get('binding') or {};stats=observed.get('stats') or {}
            if (key!=hashlib.sha256(json.dumps(owner,sort_keys=True).encode()).hexdigest()
                    or owner.get('role')!='postclose' or owner.get('pid')!=binding['pid']
                    or owner.get('boot_id')!=binding['boot_id']
                    or owner.get('resolved_root')!=binding['resolved_root']
                    or owner.get('lexical_root')!=binding['lexical_root']
                    or owner.get('day') not in {native['source_date'],proof['target_date']}
                    or stats.get('pid')!=binding['pid']):
                raise ValueError('startup_main_digest_session_owner_changed')
    manifests = closure.get('manifests')
    preserved=_preserved_native_sources(proof)
    if not isinstance(manifests, dict) or len(manifests)>16 or not (manifests or preserved):
        raise ValueError('startup_main_manifest_closure_invalid')
    for ident, observed in manifests.items():
        manifest = _json(observed['path'])
        if (_sha(observed['path']) != observed['sha256']
                or manifest.get('artifact_content_sha256') != ident
                or ident != _digest({k: v for k, v in manifest.items() if k != 'artifact_content_sha256'})
                or observed.get('bundle_sha256') != proof['policy_sha256']
                or manifest.get('base_bundle_sha256') != proof['policy_sha256']
                or observed.get('target_date') != proof['target_date']):
            raise ValueError('startup_main_manifest_binding_invalid')
        paths = {ref['path'] for ref in manifest['sources']}
        paths.update(manifest['ledger_pack_paths']); paths.update(manifest['baseline_dependency_paths'])
        readers = proof.get('native_reader_code_sources', {})
        if not isinstance(readers, dict) or len(readers) > 128:
            raise ValueError('startup_main_native_reader_sources_invalid')
        selected = Path(proof['selected_release_root'])
        for relative, digest in readers.items():
            path = selected / relative
            if (not relative.startswith('src/') or '..' in Path(relative).parts
                    or path.resolve(strict=True) != path or path.suffix != '.py'
                    or proof['source_hashes'].get(str(path)) != digest or _sha(path) != digest):
                raise ValueError('startup_main_native_reader_source_changed')
            paths.add(str(path))
        dependencies = observed.get('dependencies')
        if (not isinstance(dependencies, list) or len(dependencies) > 8192
                or len(dependencies) != len(paths) or {v[0] for v in dependencies} != paths):
            raise ValueError('startup_main_manifest_dependency_set_changed')
        for path, signature in dependencies:
            if json.loads(json.dumps(N._signature(path))) != signature:
                raise ValueError('startup_main_manifest_dependency_changed')
        frozen_root = manifest['frozen_validator_root']
        from src.engine.scalping import reversal_auxiliary_next_session as A
        inventory = closure.get('frozen_inventories', {}).get(frozen_root)
        frozen = closure.get('frozen_validations', {}).get(manifest['source_manifest']['path'])
        if (inventory != manifest['frozen_inventory'] or not inventory
                or _git_head(frozen_root) != manifest['frozen_validator_commit']
                or not isinstance(frozen, dict) or frozen.get('root') != frozen_root
                or frozen.get('bundle_path') != manifest['source_bundle']['path']
                or frozen.get('result') != manifest['frozen_validation']
                or frozen.get('invocation') != dict(executable=str(Path(frozen_root)/'.venv/bin/python'),
                    arguments=['-B','-c'],script_sha256=hashlib.sha256(A._FROZEN_SCRIPT.encode()).hexdigest(),
                    cwd=frozen_root,source_manifest=manifest['source_manifest']['path'],
                    source_bundle=manifest['source_bundle']['path'],
                    environment=dict(PYTHONPATH=frozen_root,PYTHONDONTWRITEBYTECODE='1'),
                    parent_environment='sanitized_p5_native_verification')):
            raise ValueError('startup_main_frozen_native_validation_unbound')
        # Original frozen source bytes are in native dependency signatures and
        # are also rehashed by the native prepare validator below.
        if not set(inventory).issubset(paths):
            raise ValueError('startup_main_frozen_inventory_incomplete')
        if json.loads(json.dumps(A._database_signature(manifest))) != observed['database']:
            raise ValueError('startup_main_manifest_database_changed')
    _native_logical_sources(proof)


def _native_logical_sources(proof, *, verify_ledger=False):
    """Finite selected-ledger evidence, never a byte hash of its global DB."""
    from src.engine.infrastructure.validation_digest_session import identity
    from src.engine.scalping import reversal_auxiliary_next_session as A
    from src.engine.scalping import reversal_auxiliary_input_transition as J
    from src.engine.ai import offline_comparison_store as S
    native = proof['native_verification']
    if (native.get('status') != 'pass' or native.get('findings')
            or _native_main_basis(native) is None
            or proof.get('delegation_basis') != _native_main_basis(native)):
        raise ValueError('startup_logical_native_validation_required')
    result = {}
    observed_manifests = proof['closure']['manifests']
    if (not isinstance(observed_manifests, dict) or len(observed_manifests)>16
            or not (observed_manifests or _preserved_native_sources(proof))):
        raise ValueError('startup_logical_manifest_set_invalid')
    for ident, observed in observed_manifests.items():
        manifest = _json(observed['path'])
        if (_sha(observed['path']) != observed['sha256']
                or manifest.get('artifact_content_sha256') != ident
                or ident != _digest({k:v for k,v in manifest.items() if k != 'artifact_content_sha256'})
                or manifest['base_bundle_sha256'] != proof['policy_sha256']
                or observed['target_date'] != proof['target_date']):
            raise ValueError('startup_logical_manifest_changed')
        database = json.loads(json.dumps(A._database_signature(manifest)))
        if database != observed['database']:
            raise ValueError('startup_logical_database_changed')
        identities = observed.get('database_source_identities') or {}
        if set(identities) != {v[0] for v in (database or ()) if v is not None}:
            raise ValueError('startup_logical_database_identity_set_changed')
        if database and verify_ledger:
            with S.Store(manifest['ledger_data_root'], readonly=True) as store:
                store.db.execute('BEGIN')
                actual = J._ledger_fingerprint(store, manifest['ledger_metadata'])
            if (actual != manifest['ledger_metadata']['fingerprint_sha256']
                    or json.loads(json.dumps(A._database_signature(manifest))) != database):
                raise ValueError('startup_logical_ledger_changed')
        if database and manifest.get('policy_data_root') != str(Path(proof['policy_path']).parents[3]):
            raise ValueError('startup_logical_data_root_changed')
        for index, signature in enumerate(database or ()):
            if signature is None:
                continue
            path = signature[0]
            if identity(path) != identities[path]:
                raise ValueError('startup_logical_database_identity_changed')
            row = result.setdefault(path,dict(schema='startup_native_logical_source_v1', path=path,
                source_kind='sqlite_ledger_container' if index == 0 else 'sqlite_ledger_wal',
                identity=identities[path], native_signature=signature, manifest_proofs={},
                policy_data_root=manifest['policy_data_root'],
                source_run_id=proof['closure']['run_id'], target_date=proof['target_date'],
                policy_sha256=proof['policy_sha256'], runtime_effect=False, allowed_runtime_apply=False))
            if row['identity'] != identities[path] or row['native_signature'] != signature:
                raise ValueError('startup_logical_database_conflict')
            row['manifest_proofs'][ident] = dict(path=observed['path'],sha256=observed['sha256'],
                ledger_data_root=manifest['ledger_data_root'],
                ledger_metadata_sha256=_digest(manifest['ledger_metadata']),
                ledger_fingerprint_sha256=manifest['ledger_metadata']['fingerprint_sha256'])
    return {path:{**row,'receipt_sha256':_digest(row)} for path,row in result.items()}


def preparation_logical_sources():
    """P5-only typed sources; ordinary/native runtime callers keep full reads."""
    proof = _main_context()
    return {} if proof is None else _native_logical_sources(proof)


def verify_preparation_logical_sources(proof, receipts):
    """Parent/P6 exact-set check after request binding; recheck finite native rows.

    Callers retain their original request, release, selector and source CAS.
    No old digest TTL or cached verification verdict is reused here.
    """
    expected = _native_logical_sources(proof, verify_ledger=True)
    if not isinstance(receipts, dict) or receipts != expected:
        raise ValueError('startup_logical_source_set_changed')
    return expected


def _main_proof(proof, request):
    if (not isinstance(proof, dict) or proof.get('schema') != MAIN_PROOF_SCHEMA
            or proof.get('target_date') != request['target_date']
            or proof.get('execution_release_root') != request['execution_release_root']
            or proof.get('execution_release_commit') != request['execution_release_commit']
            or proof.get('closure', {}).get('run_id') != request['run_id']
            or proof.get('policy_effect') != 'unchanged'
            or proof.get('delegation_basis') != _native_main_basis(proof.get('native_verification') or {})
            or _native_main_basis(proof.get('native_verification') or {}) is None
            or (proof.get('native_verification', {}).get('validation_scope') == 'intraday_preserved_historical_generation'
                and proof['native_verification'].get('preserved_preopen_commit') != request['manifest'].get('selected_release_sha'))
            or any(proof.get(k) is not False for k in ('runtime_effect', 'allowed_runtime_apply', 'actual_pid_consumed'))
            or any((request.get('expected_policy_hashes') or {}).get(k) != proof.get('policy_sha256')
                   for k in ('main_machine', 'main_auxiliary'))):
        raise ValueError('startup_main_preparation_proof_invalid')
    sources = proof.get('source_hashes')
    _check_sources(sources)
    if any(request['source_hashes'].get(path) != value for path, value in sources.items()):
        raise ValueError('startup_main_preparation_sources_unbound')
    data = Path(request['data_root'])
    path = data / 'runtime/mechanistic_entry_policy/candidates' / ('policy_' + request['target_date'] + '.json')
    if proof.get('policy_path') != str(path) or _sha(path) != proof.get('policy_file_sha256'):
        raise ValueError('startup_main_preparation_policy_changed')
    bundle = _json(path)
    if bundle.get('bundle_sha256') != proof['policy_sha256'] or _main_inventories(bundle) != proof.get('inventories'):
        raise ValueError('startup_main_preparation_inventory_changed')
    selected = Path(proof['selected_release_root'])
    if _git_head(selected) != proof['selected_release_commit']:
        raise ValueError('startup_main_preparation_selected_changed')
    selector = _json(data / 'runtime/runtime_release_selection.json')
    if (selector.get('release_root') != str(selected)
            or selector.get('git_commit') != proof['selected_release_commit']):
        raise ValueError('startup_main_preparation_selector_changed')
    expected, actual = proof['original_code_hashes'], proof['runtime_code_hashes']
    required = {}
    inventory_attestations = {}
    for item in proof['inventories']:
        if not _hex(item['origin_commit'], 40):
            raise ValueError('startup_main_inventory_origin_invalid')
        values = {_code_path(name): value for name, value in item['expected'].items()}
        inventory_attestations[item['bundle_sha256']] = dict(origin_commit=item['origin_commit'],
            code_hashes=values)
        for name, value in item['expected'].items():
            relative = _code_path(name)
            required[relative] = _sha(selected / relative)
        _pairs(values, {name: actual[name] for name in values})
    if inventory_attestations != proof.get('inventory_git_attestations'):
        raise ValueError('startup_main_inventory_git_attestation_changed')
    histories = {}
    for ident, observed in proof['closure']['manifests'].items():
        manifest = _json(observed['path'])
        histories[ident] = _historical_code_refs(manifest)
        for relative, ref in histories[ident].items():
            if sources.get(ref['path']) != ref['sha256']:
                raise ValueError('startup_main_historical_code_unbound')
            value = _sha(selected / relative)
            if required.setdefault(relative, value) != value:
                raise ValueError('startup_main_origin_inventory_conflict')
        for field in ('next_session_code_hashes', 'reader_code_hashes'):
            for name, value in manifest[field].items():
                relative = _code_path(name)
                selected_hash = _sha(selected / relative)
                if (value != selected_hash and not reviewed_preparation_pair(relative, value, selected_hash)
                        or required.setdefault(relative, selected_hash) != selected_hash):
                    raise ValueError('startup_main_origin_inventory_conflict:' + relative)
    for relative in REVIEWED_PREPARATION_SOURCES:
        old = _sha(selected / relative)
        if required.setdefault(relative, old) != old:
            raise ValueError('startup_main_origin_inventory_conflict')
    if required != expected or histories != proof.get('historical_semantic_code_sources'):
        raise ValueError('startup_main_exact_code_closure_required')
    _pairs(expected, actual)
    for refs in histories.values():
        _pairs({name: ref['sha256'] for name, ref in refs.items()},
               {name: actual[name] for name in refs})
    for relative, old in expected.items():
        if (_sha(selected / relative) != old or _sha(ROOT / relative) != actual[relative]
                or sources.get(str(selected / relative)) != old
                or sources.get(str(ROOT / relative)) != actual[relative]):
            raise ValueError('startup_main_preparation_code_changed')
    _check_native_closure(proof)


def _request_identity(path):
    from src.engine.infrastructure.validation_digest_session import identity
    return identity(path)


def _anchor_identities_unchanged(anchors):
    """Compare all files while checking shared lexical parents once per pass."""
    parents = {}
    def parent_row(name):
        value = os.lstat(name)
        row = [name, value.st_dev, value.st_ino, value.st_mode, value.st_uid]
        if stat.S_ISLNK(value.st_mode):
            row += [value.st_ctime_ns, os.readlink(name)]
        return row
    for name, before in anchors.items():
        if name != before[0]:
            return False
        if before[0] != before[1]:
            if _request_identity(name) != before:
                return False
            continue
        value = os.lstat(name)
        if [value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns,
                value.st_ctime_ns, value.st_mode, value.st_uid] != before[2:9]:
            return False
        for row in before[9]:
            if row[0] not in parents:
                parents[row[0]] = parent_row(row[0])
            if parents[row[0]] != row:
                return False
    return all(parent_row(name) == row for name, row in parents.items())


def _main_context(*, digest_only=False):
    global _CONTEXT
    if _CONTEXT is None:
        return None
    try:
        c = _CONTEXT
        if c.get('valid') is not True:
            raise ValueError('startup_code_context_invalid')
        _isolation(c['request'])
        if (os.getpid() != c['pid'] or _request_identity(c['request_path']) != c['request_identity']
                or (not digest_only and (_git_head(ROOT) != c['request']['execution_release_commit']
                    or _sha(c['request_path']) != c['request_sha256']))):
            raise ValueError('startup_code_context_execution_changed')
        proof = c['request'].get('main_preparation_code_handoff')
        if not isinstance(proof, dict):
            raise ValueError('startup_main_preparation_proof_required')
        if (_git_head(proof['selected_release_root']) != proof['selected_release_commit']
                or _git_head(ROOT) != c['request']['execution_release_commit']
                or _sha('/proc/self/mountinfo') != c['main_mountinfo_sha256']
                or not _anchor_identities_unchanged(c['main_anchor_identities'])
                or _sha('/proc/self/mountinfo') != c['main_mountinfo_sha256']):
            raise ValueError('startup_main_preparation_anchor_changed')
        return proof
    except (OSError, ValueError, KeyError, TypeError):
        _CONTEXT = {'valid': False}
        raise


def validation_raw_vote_sources(data_root, source_date):
    """Keep isolated native vote validation on its bounded raw JSONL reader.

    Ordinary runtime/research retains the indexed reader. This selects I/O,
    never a semantic verdict or an exception to the original raw guards.
    """
    if _CONTEXT is None:
        return False
    proof = _main_context()
    request = _CONTEXT['request']
    if (str(Path(data_root).resolve()) != request['data_root']
            or date.fromisoformat(source_date).isoformat() != source_date
            or source_date > proof['native_verification']['source_date']
            or not source_date < request['target_date']):
        raise ValueError('startup_raw_vote_source_scope_invalid')
    return True


def validation_future_vote_snapshot(data_root, source_date):
    """Permit only a native future-tail snapshot inside the isolated child."""
    if _CONTEXT is None:
        return False
    _main_context()
    request = _CONTEXT['request']
    proof = request['candidate_code_handoffs'].get('main_stop')
    if not isinstance(proof, dict):
        raise ValueError('startup_stop_snapshot_policy_required')
    _proof(proof, 'main_stop', request)
    receipt = request['manifest']['main_stop_confirmation_receipt']
    if (str(Path(data_root).resolve()) != request['data_root']
            or receipt.get('source_date') != source_date or not source_date < request['target_date']):
        raise ValueError('startup_stop_snapshot_scope_invalid')
    return True


def _delay_selection_records(proof):
    from src.engine.infrastructure.validation_digest_session import identity
    records = proof['closure'].get('delay_selections', {})
    if not isinstance(records, dict) or len(records) > 16:
        raise ValueError('startup_delay_selection_closure_invalid')
    origin = proof.get('delay_inventory_git_attestation')
    if records:
        selected, native_commit = _native_verifier_code(proof)
        declaration = selected/_DELAY_CONTRACT_OWNER
        if (not isinstance(origin, dict) or origin.get('schema') != 'startup_delay_native_inventory_git_v1'
                or origin.get('origin_commit') != native_commit
                or origin.get('selected_release_root') != str(selected)
                or selected.resolve(strict=True) != selected
                or _git_head(selected) != native_commit
                or origin.get('declaration_path') != str(declaration)
                or declaration.resolve(strict=True) != declaration
                or _sha(declaration) != origin.get('declaration_sha256')
                or proof['source_hashes'].get(str(declaration)) != origin.get('declaration_sha256')
                or origin.get('contract_paths') != _delay_contract_paths(_read(declaration))
                or not isinstance(origin.get('code_hashes'), dict)
                or set(origin['code_hashes']) != set(origin['contract_paths'])):
            raise ValueError('startup_delay_native_inventory_attestation_invalid')
    for key, item in records.items():
        if (not isinstance(item, dict) or item.get('schema') != 'startup_native_delay_selection_v1'
                or item.get('run_id') != proof['closure']['run_id']
                or item.get('parent_full_selection_recomputed') is not True
                or item.get('child_recomputed') is not False
                or item.get('target_date') not in (None, proof['target_date'])
                or key != _digest([item.get('policy_sha256'), item.get('target_date')])
                or set(item.get('artifacts', {})) != {'policy', 'report'}):
            raise ValueError('startup_delay_selection_closure_invalid')
        root = Path(item['evidence_root'])
        if root.resolve(strict=True) != root or root.is_symlink():
            raise ValueError('startup_delay_evidence_alias')
        values = {}
        for name, ref in item['artifacts'].items():
            path = root / (name + '.json')
            if (ref.get('path') != str(path) or identity(path) != ref.get('identity')
                    or proof['source_hashes'].get(str(path)) != ref.get('sha256')
                    or _sha(path) != ref.get('sha256')):
                raise ValueError('startup_delay_artifact_generation_changed')
            values[name] = _json(path)
        policy, report = values['policy'], values['report']
        data_root = Path(proof['policy_path']).parents[3]
        expected_root = data_root/'threshold_cycle/pre_submit_delay_policy/generations'/_digest([report, policy])
        if root != expected_root:
            raise ValueError('startup_delay_policy_generation_unbound')
        if (item.get('documents_sha256') != _digest([policy, report])
                or item.get('report_sha256') != _digest(report)
                or item.get('policy_sha256') != policy.get('policy_sha256')
                or item.get('source_sha256') != policy.get('source_sha256')
                or item.get('code_contract_sha256') != policy.get('code_contract_sha256')
                or item.get('effective_from') != policy.get('effective_from')
                or item.get('expires_on') != policy.get('expires_on')
                or not item['effective_from'] <= proof['target_date'] <= item['expires_on']
                or item.get('tree_refs') != {key: report.get(key) for key in
                    ('qualified_projection_ref', 'partitions_ref', 'cells_ref')}):
            raise ValueError('startup_delay_selection_binding_invalid')
        inventory = item.get('native_code_inventory')
        if (not isinstance(inventory, dict) or inventory != origin['code_hashes']
                or _digest(inventory) != item.get('native_code_sha256')):
            raise ValueError('startup_delay_native_code_inventory_invalid')
        for relative, expected in inventory.items():
            path = selected / relative
            if (path.resolve(strict=True) != path or not _hex(expected)
                    or proof['source_hashes'].get(str(path)) != expected or _sha(path) != expected):
                raise ValueError('startup_delay_native_code_changed')
    return records


def validate_preparation_delay_selection(policy, report, *, target_date=None):
    """Recheck source trees; delegate only the parent's observed SQL rebuild.

    The same invocation's native full verification executed that rebuild
    before isolation. Ordinary consumers retain the complete native algorithm.
    """
    proof = _main_context(digest_only=True)
    if proof is None:
        return False
    request = _CONTEXT['request']
    contract = request['candidate_code_handoffs'].get('pre_submit_delay') or {}
    bound = request['manifest'].get('pre_submit_delay_handoff') or {}
    if (contract.get('policy_sha256') != policy.get('policy_sha256')
            or bound.get('policy_path') != str(getattr(policy, 'evidence_root', '') / Path('policy.json'))
            or target_date not in (None, request['target_date'])):
        raise ValueError('startup_delay_request_binding_invalid')
    records = _delay_selection_records(proof)
    matched = [v for v in records.values() if v['policy_sha256'] == policy.get('policy_sha256')]
    root = getattr(report, 'evidence_root', None)
    if (not matched or root is None or getattr(policy, 'evidence_root', None) != root
            or any(v['evidence_root'] != str(root) or v['documents_sha256'] != _digest([policy, report])
                   for v in matched)):
        raise ValueError('startup_delay_selection_unobserved_or_changed')
    sources = _delay_tree_sources(root, report)
    delegated = _CONTEXT['delegation'].setdefault('delay_selections', {})
    delegated[policy['policy_sha256']] = dict(
        parent_full_selection_recomputed=True, child_recomputed=False,
        child_headers_and_physical_logical_trees_reverified=True,
        documents_sha256=_digest([policy, report]), evidence_root=str(root), source_hashes=sources)
    return True


def _delay_tree_sources(root, report):
    """Reverify the native trees, including every nested membership leaf."""
    from src.engine.lifecycle import research_storage as storage
    from src.engine.lifecycle.research_input_budget import Claim
    from src.engine.infrastructure.validation_digest_session import identity
    sources = {}
    def physical(ref, depth=0):
        if depth > 16:
            raise ValueError('research_tree_depth_invalid')
        if ref.get('kind') == 'inline':
            return
        if type(ref.get('size')) is not int or not 0 <= ref['size'] <= 4*1024*1024:
            raise ValueError('research_shard_generation_changed')
        path = storage.safe_path(root, ref['path'])
        before = identity(path)
        with Claim(ref['size']*8):
            raw = _read(path, maximum=ref['size'])
            if (len(raw) != ref['size'] or hashlib.sha256(raw).hexdigest() != ref['sha256']
                    or identity(path) != before):
                raise ValueError('startup_delay_shard_generation_changed')
            if sources.setdefault(str(path), ref['sha256']) != ref['sha256']:
                raise ValueError('startup_delay_shard_reference_conflict')
            body = json.loads(raw)
            for child in body.get('children', []):
                physical(child, depth+1)
    for key in ('qualified_projection_ref', 'partitions_ref', 'cells_ref'):
        for row in storage.iter_tree(root, report[key]):
            if key == 'partitions_ref':
                for _ in storage.iter_tree(root, row['membership']):
                    pass
                physical(row['membership'])
        physical(report[key])
    return sources


def preparation_delay_source_hashes():
    if _main_context(digest_only=True) is None:
        return {}
    sources = {}
    for item in _CONTEXT['delegation'].get('delay_selections', {}).values():
        for path, sha in item['source_hashes'].items():
            if sources.setdefault(path, sha) != sha:
                raise ValueError('startup_delay_child_source_conflict')
    return sources


def verify_preparation_delay_delegation(proof, delegation, request, consumer):
    """Parent mandatory exact-set check; also reusable for fresh source CAS."""
    records = _delay_selection_records(proof)
    bound = request['manifest'].get('pre_submit_delay_handoff') or {}
    ident = bound.get('policy_sha256')
    matched = [v for v in records.values() if v['policy_sha256'] == ident]
    actual = delegation.get('delay_selections', {})
    if not matched:
        configured = _json(bound['policy_path']) if bound.get('policy_path') else {}
        if actual or configured.get('storage_schema') == 'pre_submit_delay_sharded_evidence_v3':
            raise ValueError('startup_delay_child_selection_unobserved')
        return
    if set(actual) != {ident} or consumer.get('status') != 'loaded':
        raise ValueError('startup_delay_child_selection_missing')
    item = matched[0]
    if item['artifacts']['policy']['path'] != bound.get('policy_path'):
        raise ValueError('startup_delay_child_policy_unbound')
    report = _json(item['artifacts']['report']['path'])
    sources = _delay_tree_sources(Path(item['evidence_root']), report)
    expected = dict(parent_full_selection_recomputed=True, child_recomputed=False,
        child_headers_and_physical_logical_trees_reverified=True,
        documents_sha256=item['documents_sha256'],evidence_root=item['evidence_root'],source_hashes=sources)
    if actual[ident] != expected or any(consumer.get('source_hashes', {}).get(p) != s for p,s in sources.items()):
        raise ValueError('startup_delay_child_selection_changed')


def verify_validation_main_code(bundle, paths, actual):
    proof = _main_context()
    if proof is None:
        return False
    item = next((v for v in proof['inventories'] if v['bundle_sha256'] == bundle.get('bundle_sha256')), None)
    family = bundle.get('continuous_reversal') or {}
    expected = family.get('contract_file_sha256')
    if (item is None or item['expected'] != expected or item['schema'] != family.get('schema')
            or item['target_date'] != bundle.get('target_date')
            or set(paths) != set(expected) or set(actual) != set(expected)):
        raise ValueError('startup_main_native_inventory_unbound')
    for name, old in expected.items():
        relative = _code_path(name)
        if (str(Path(paths[name]).resolve(strict=True)) != str(ROOT / relative)
                or proof['runtime_code_hashes'].get(relative) != actual[name]
                or _sha(paths[name]) != actual[name]):
            raise ValueError('startup_main_native_code_unbound')
    _pairs({_code_path(name): old for name, old in expected.items()},
           {_code_path(name): value for name, value in actual.items()})
    return True


def validation_auxiliary_preparation(manifest, bundle, data_root):
    proof = _main_context()
    if proof is None:
        return None
    item = proof['closure']['manifests'].get(manifest.get('artifact_content_sha256'))
    if (not isinstance(item, dict) or bundle.get('bundle_sha256') != proof['policy_sha256']
            or bundle.get('target_date') != proof['target_date']
            or str(Path(data_root).resolve()) != _CONTEXT['request']['data_root']
            or _json(item['path']) != manifest or _sha(item['path']) != item['sha256']):
        raise ValueError('startup_main_auxiliary_preparation_unbound')
    _check_native_closure(proof)
    ident = manifest['artifact_content_sha256']
    if ident not in _CONTEXT['delegation']['auxiliary_manifests']:
        _CONTEXT['delegation']['auxiliary_manifests'].append(ident)
    historical = proof['historical_semantic_code_sources'][ident]
    original = {**proof['original_code_hashes'], **{name: ref['sha256'] for name, ref in historical.items()}}
    for field in ('next_session_code_hashes', 'reader_code_hashes'):
        for name, digest in manifest[field].items():
            relative = _code_path(name)
            if relative not in historical:
                original[relative] = digest
    return dict(manifest=manifest, frozen_inventory=manifest['frozen_inventory'],
        frozen_validation=manifest['frozen_validation'],
        original_code_hashes=original, runtime_code_hashes=proof['runtime_code_hashes'],
        delegation_basis=proof['delegation_basis'])


class _PreparationDigests:
    """Read-only, process-bound reuse of bytes hashed by the same P5 intake."""
    @property
    def binding(self):
        if _main_context() is None:
            raise ValueError('startup_code_context_required')
        # This adapter must never enroll source generations as a postclose
        # producer; native readers still execute against the parent byte proof.
        return {'role': 'startup_validation'}

    def digest(self, path):
        if _CONTEXT is None:
            return None
        if _CONTEXT.get('valid') is not True:
            raise ValueError('startup_code_context_invalid')
        item = _CONTEXT['request'].get('main_preparation_code_handoff')
        if not isinstance(item, dict):
            return None
        entry = item['closure']['digest_entries'].get(str(Path(path).absolute()))
        if entry is None:
            return None
        proof = _main_context(digest_only=True)
        if proof is None:
            return None
        from src.engine.infrastructure.validation_digest_session import identity
        if identity(path) != entry['identity'] or not 0 <= time.time() - entry['created'] <= 600:
            raise ValueError('startup_main_digest_generation_changed')
        _CONTEXT['delegation']['digest_reused_reads'] += 1
        _CONTEXT['delegation']['digest_reused_bytes'] += entry['identity'][4]
        return entry['digest']


def preparation_source_digest(path):
    """Only the P5 parent attestation; ordinary digest sessions do not opt in."""
    return _PreparationDigests().digest(path)


def validation_delegation_receipt():
    proof = _main_context()
    if proof is None:
        return None
    return dict(schema='startup_native_validation_delegation_v1',
        basis=proof['delegation_basis'], source_native_pid=proof['closure']['digest_binding']['pid'],
        target_date=proof['target_date'], policy_sha256=proof['policy_sha256'],
        run_id=proof['closure']['run_id'], request_sha256=_CONTEXT['request']['request_sha256'],
        parent_validation_scope=proof['native_verification']['validation_scope'],
        child_semantic_validation='native_validators_executed',
        **_CONTEXT['delegation'], runtime_effect=False, actual_pid_consumed=False,
        allowed_runtime_apply=False)
