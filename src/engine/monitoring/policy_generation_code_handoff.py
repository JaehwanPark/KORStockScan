"""Report-only capability projection across an exactly reviewed code successor.

Ownership: monitoring, separate from native report/policy publication. Original
contracts and source bytes remain historical; no strategy authority is granted.
"""
from copy import deepcopy
from pathlib import Path

from src.engine.monitoring import policy_generation_contract as generation
from src.engine.monitoring import policy_generation_validation as validation

# 92785b7da and the reviewed 86f789693 native-arm completion successor change
# entry paths in the shared handler, not either family publication or policy.
# The carried-stop reader partitions future unconsumed observations; 40b931254
# scopes the approved Main weak vetoes without changing either family producer.
# All components remain bound by the complete generation hashes; current fixture
# evidence is independently required. No historical contract is reclassified.
# Review: docs/audits/main-cumulative-holding-integration-deployment-2026-10-15.md.
# Preset/cost-clock and cumulative auxiliary changes extend exact review to
# entry-cancel-wait and auxiliary; every successor needs new isolated fixtures.
# The holding-context snapshot successor changes only the source-only observer's
# concurrent reads. Rising/holding require fresh fixtures for the new bytes.
# Review: docs/audits/main-holding-context-dictionary-race-repair-2026-10-15.md.
# The carried-stop reader now locks future-only vote snapshots; the holding
# capability remains bound to a fresh exact-generation fixture.
# Review: docs/audits/main-finalization-live-vote-read-race-repair-2026-10-15.md.
# Async session-boundary rejection changes shared-handler bytes only. Preserve
# route/order guards and require fresh rising/holding fixtures for this successor.
# Review: docs/audits/main-entry-price-progress-deployment-review-2026-10-15.md.
# The terminal KST/custody repair changes shared-handler bytes. Verify fresh
# fixtures while retaining all original reports and unresolved terminal evidence.
# The reviewed sealed-prefix and overnight terminal receipt successor preserves
# historical source bytes and requires its own fresh holding capability fixture.
# Source-gap and mandatory first-crossing repair: exact code pairs only.
# Fresh network-denied fixtures attest every changed generation.
# Review: docs/audits/main-postclose-source-gap-final-release-review-2026-10-16.md.
# Probe partial custody repair changes shared handler/receipt bytes only.
# Fresh fixtures bind the successor; historical source reports remain unchanged.
# Review: docs/audits/main-probe-partial-integrated-deployment-review-2026-10-16.md.
# Long4/fixed-watch and 04c holding/replay integration; original reports stay unchanged.
# Review: docs/audits/long4-source-retention-integration-review-2026-10-16.md.
REVIEWED_SUCCESSORS = {
    'entry_cancel_wait': (
        'd8583947a62ffe15318b2819f6f4824b8835a7fc5865c5b00f85b8eb427620b0',
        'a164112c82cfa2d225be971f5197d0a7bff9dee07d4223ea7a3b3ccce20f3de4'),
    'rising_missed': (
        'dfe2d56deef10ebaf4f2aa6e3edd6215f769d08ba8ac123808459c2cc8fb720f',
        '684090396e36144e6b79a33aacf55f8f63c3bd9260e534d58e2aefcdcd30f2e9'),
    'auxiliary': (
        '88a496105946f292ae3c85028be6276009738742a0916f7c9965c9c9ba6959df',
        'df0247a1bbed3e52af5b315911a1051c1bb94f8d39a444e04e341b23dcf6f786'),
    'holding_vote': (
        'b2087e97e70fc145620d3440c4fddafd633ab8e45d3aa492fffec17a7b04bcab',
        '2cdbab10ad57c817ba2117d43699ba2fe79a96fe73e5e00e5667bacaeffd2d3e'),
}

# The next dated native report already carries the formerly reviewed successor.
# Preserve that report too; do not relabel it as the older source generation.
REVIEWED_PRESERVED_SOURCE_SUCCESSORS = {
    # Exact 10/15 native reports retained after source-census and residual
    # custody repairs. Revalidate their original fixtures and source bodies;
    # current capability does not promote their comparison/selection state.
    'entry_cancel_wait': (
        'b2a2017deb606554fbe1c9d481426786b3a8ab463c948ee84cd8ab856eddfca0',
        'a164112c82cfa2d225be971f5197d0a7bff9dee07d4223ea7a3b3ccce20f3de4'),
    'rising_missed': (
        'dde49a32b7299deabf981e9f3a734a9da3019ba3f4e3eb7abbaff91dd3d01fa3',
        '684090396e36144e6b79a33aacf55f8f63c3bd9260e534d58e2aefcdcd30f2e9'),
    'holding_vote': (
        '5658a73a4aeb866c3124370eddc500ce27dd2e15589ba2ef4d7c35c7231a83c2',
        '2cdbab10ad57c817ba2117d43699ba2fe79a96fe73e5e00e5667bacaeffd2d3e'),
}


# The actual 4c65523b2 source generation is also preserved if already reported.
REVIEWED_DEPLOYED_SOURCE_SUCCESSORS = {
    'entry_cancel_wait': ('6d6a294941f6337d48420514d40e36891d25b44dc09bd914be0831d897794d4c', 'a164112c82cfa2d225be971f5197d0a7bff9dee07d4223ea7a3b3ccce20f3de4'),
    'rising_missed': ('0f6c455328de656c920956be0b2a24fec57db08f8b4e7b3e2fa7db43249ff7ed', '684090396e36144e6b79a33aacf55f8f63c3bd9260e534d58e2aefcdcd30f2e9'),
    'auxiliary': ('711184e6d93f27e3d8f4bdd97598f4880f752332f850763b32b434560b460f8e', 'df0247a1bbed3e52af5b315911a1051c1bb94f8d39a444e04e341b23dcf6f786'),
    'holding_vote': ('e213bbe524aa7575f8e9c784cf43db77b9c194dee5bfc03b943a8175fc655278', '2cdbab10ad57c817ba2117d43699ba2fe79a96fe73e5e00e5667bacaeffd2d3e'),
}


# Delay situation/zero-cell observer repair touches shared handler metadata.
# Preserve the selected predecessor's report generation and require a new fixture.
# Review: docs/audits/pre-submit-semantic-implementation-review-2026-10-16.md.
REVIEWED_DELAY_SOURCE_SUCCESSORS = {'rising_missed': ('ea1ac91b6e080d96f3a0d61dca47575c101862ba6fe77fed36fc6170687f3e08', '684090396e36144e6b79a33aacf55f8f63c3bd9260e534d58e2aefcdcd30f2e9'), 'holding_vote': ('dfd762fa2b9d15799e4951bc5624effa58f8efdec29cb85939ba9d5e21765d58', '2cdbab10ad57c817ba2117d43699ba2fe79a96fe73e5e00e5667bacaeffd2d3e')}


def _historical_fixture(contract, data, family):
    """Preserve a prior fixture without using it to certify the successor."""
    reference = contract.get('fixture_receipt')
    if reference is None:
        return None
    path = Path(data)/'report/postclose_generation_validation'/(
        family+'_'+contract['code_sha256']+'.json')
    if not isinstance(reference, dict) or reference.get('path') != str(path):
        raise ValueError('successor_historical_fixture_path_invalid')
    payload, sha = validation.bounded_object(path, 65536)
    if (path.is_symlink() or sha != reference.get('sha256')
            or payload.get('schema') != 'postclose_generation_fixture_receipt_v1'
            or payload.get('family') != family or payload.get('status') != 'pass'
            or payload.get('code_sha256') != contract['code_sha256']
            or not payload.get('closure_tests') or payload.get('unresolved_findings') != []
            or payload.get('receipt_sha256') != generation.digest(
                {k:v for k,v in payload.items() if k != 'receipt_sha256'})
            or payload.get('runtime_effect') is not False
            or payload.get('actual_pid_consumed') is not False
            or payload.get('actual_profit_verified') is not False
            or payload.get('allowed_runtime_apply', False) is not False):
        raise ValueError('successor_historical_fixture_invalid')
    return reference


def current_fixture_observation(observed, data):
    family = observed.get('family')
    pair = REVIEWED_SUCCESSORS.get(family)
    actual_pair = (observed.get('code_sha256'), generation.code_generation(family))
    preserved = REVIEWED_PRESERVED_SOURCE_SUCCESSORS.get(family)
    if preserved and actual_pair == preserved:
        pair = preserved
    deployed = REVIEWED_DEPLOYED_SOURCE_SUCCESSORS.get(family)
    if deployed and actual_pair == deployed:
        pair = deployed
    delay = REVIEWED_DELAY_SOURCE_SUCCESSORS.get(family)
    if delay and actual_pair == delay:
        pair = delay
    if not pair or actual_pair != pair:
        return validation.current_fixture_observation(observed, data)
    if (observed.get('status') != 'unverified' or observed.get('findings') != ['policy_generation_unverified']
            or observed.get('missing_components') != [] or observed.get('observation_complete') is not True
            or observed.get('native_validated') is not False):
        return observed
    try:
        data = Path(data)
        fixture, reference = validation.verify_fixture(data, family)
        path = validation.native_report_path(data, family, observed['source_date'])
        if Path(observed['artifact']) != path:
            raise ValueError('successor_report_path_invalid')
        payload, report_sha = validation.bounded_object(path, 8*1024*1024)
        native = payload['holding_path_vote_replay'] if family == 'holding_vote' else payload
        contract = native['policy_generation']
        if observed.get('binding_repair') is not None:
            if family != 'holding_vote':
                raise ValueError('successor_binding_family_invalid')
            contract, binding = generation._read_holding_code_rebinding(
                data, observed['source_date'], report_sha, payload)
            if binding != observed['binding_repair']:
                raise ValueError('successor_binding_changed')
        original = generation.inspect(contract, family=family, day=observed['source_date'],
                                      payload=native, data_root=data)
        keys = ('status','findings','missing_components','observation_complete','source_generation',
                'code_sha256','contract_sha256','source_state','comparison_state','handoff_state')
        if (any(original[k] != observed.get(k) for k in keys)
                or report_sha != observed.get('report_sha256') or contract['code_sha256'] != pair[0]
                or fixture['code_sha256'] != pair[1]):
            raise ValueError('successor_historical_contract_changed')
        historical_fixture = _historical_fixture(contract, data, family)
        current = generation.native(native, family=family, day=observed['source_date'], data_root=data,
            source_state=contract['source_state'], comparison_state=contract['comparison_state'],
            handoff_state=contract['handoff_state'])
        verified = generation.inspect(current, family=family, day=observed['source_date'], payload=native, data_root=data)
        if (verified['status'] != 'verified' or current['fixture_receipt'] != reference
                or verified['source_generation'] != original['source_generation']
                or current['code_sha256'] != pair[1] or validation.file_sha(path) != report_sha):
            raise ValueError('successor_current_reader_unverified')
        if historical_fixture and validation.file_sha(historical_fixture['path']) != historical_fixture['sha256']:
            raise ValueError('successor_historical_fixture_changed')
        result = deepcopy(observed)
        result.update(status='verified', findings=[], native_validated=False,
            current_code_capability_verified=True, historical_contract_status='unverified',
            verification_basis='reviewed_code_successor_fixture_for_preserved_native_report',
            current_fixture=reference, current_capability_contract_sha256=current['contract_sha256'],
            current_capability_code_sha256=pair[1], reviewed_code_pair=list(pair))
        if historical_fixture:
            result['preserved_historical_fixture'] = historical_fixture
        result['scopes'] = {family:{k:v for k,v in result.items() if k not in {'scopes','family','source_date','artifact'}}}
        return result
    except (OSError, ValueError, KeyError, TypeError, validation.ET.ParseError) as exc:
        return dict(observed, current_fixture_status='invalid', current_fixture_reason=str(exc))
