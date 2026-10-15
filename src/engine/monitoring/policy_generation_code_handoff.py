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
# All components remain bound by the complete generation hashes; current fixture
# evidence is independently required. No historical contract is reclassified.
# Review: docs/audits/main-native-entry-arm-handoff-repair-2026-10-15.md.
REVIEWED_SUCCESSORS = {
    'rising_missed': (
        'dfe2d56deef10ebaf4f2aa6e3edd6215f769d08ba8ac123808459c2cc8fb720f',
        'd2af96d68157d270ed4fc8f44c67896180210100e0f86ddc3505c288d7470807'),
    'holding_vote': (
        'b2087e97e70fc145620d3440c4fddafd633ab8e45d3aa492fffec17a7b04bcab',
        'd0a28277da5dccdeaf07830fc426ff2cf7b9eb0ebbea35bd48ed20adbacdedd3'),
}


def current_fixture_observation(observed, data):
    family = observed.get('family')
    pair = REVIEWED_SUCCESSORS.get(family)
    if not pair or (observed.get('code_sha256'), generation.code_generation(family)) != pair:
        return validation.current_fixture_observation(observed, data)
    if (observed.get('status') != 'unverified' or observed.get('findings') != ['policy_generation_unverified']
            or observed.get('missing_components') != [] or observed.get('observation_complete') is not True
            or observed.get('native_validated') is not False):
        return observed
    try:
        data = Path(data)
        fixture, reference = validation.verify_fixture(data, family)
        relative = {'rising_missed':'rising_missed_classifier_prior/rising_missed_classifier_prior_',
                    'holding_vote':'monitor_snapshots/holding_exit_observation_'}[family]
        path = data/'report'/(relative+observed['source_date']+'.json')
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
        if (any(original[k] != observed.get(k) for k in keys) or contract.get('fixture_receipt') is not None
                or report_sha != observed.get('report_sha256') or contract['code_sha256'] != pair[0]
                or fixture['code_sha256'] != pair[1]):
            raise ValueError('successor_historical_contract_changed')
        current = generation.native(native, family=family, day=observed['source_date'], data_root=data,
            source_state=contract['source_state'], comparison_state=contract['comparison_state'],
            handoff_state=contract['handoff_state'])
        verified = generation.inspect(current, family=family, day=observed['source_date'], payload=native, data_root=data)
        if (verified['status'] != 'verified' or current['fixture_receipt'] != reference
                or verified['source_generation'] != original['source_generation']
                or current['code_sha256'] != pair[1] or validation.file_sha(path) != report_sha):
            raise ValueError('successor_current_reader_unverified')
        result = deepcopy(observed)
        result.update(status='verified', findings=[], native_validated=False,
            current_code_capability_verified=True, historical_contract_status='unverified',
            verification_basis='reviewed_code_successor_fixture_for_preserved_native_report',
            current_fixture=reference, current_capability_contract_sha256=current['contract_sha256'],
            current_capability_code_sha256=pair[1], reviewed_code_pair=list(pair))
        result['scopes'] = {family:{k:v for k,v in result.items() if k not in {'scopes','family','source_date','artifact'}}}
        return result
    except (OSError, ValueError, KeyError, TypeError, validation.ET.ParseError) as exc:
        return dict(observed, current_fixture_status='invalid', current_fixture_reason=str(exc))
