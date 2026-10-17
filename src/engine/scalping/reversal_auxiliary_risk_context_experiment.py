"""Opt-in offline observed-risk context; never a production input contract.

This separate owner preserves the SHA-pinned production RVP transformation.
It reuses received confirmation-prefix facts and exact native snapshot context.
No new thresholds, policy publication, provider calls, or order authority exist.
"""
from __future__ import annotations

import copy
import math

from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import reversal_auxiliary_causal_experiment as C
from src.engine.scalping import reversal_auxiliary_risk_role_experiment as R
from src.engine.scalping import reversal_auxiliary_research_wire as OLD_W
from src.engine.scalping import reversal_auxiliary_wire as W
from src.engine.scalping import reversal_extended_union as U

VERSION = 'auxiliary_observed_risk_context_experiment_v1'
COMMON_KEYS = ('epoch', 'symbol', 'market', 'venue', 'source_item',
               'native_epoch', 'native_sequence', 'confirmation_price', 'entry_ask')
INTERPRETATION = (
    'Descriptions of received observations ending at confirmation, not future outcomes. '
    'A positive spread is a transaction fact, not proof of a failed entry. '
    'Risk bindings permit citations; they do not assert that a risk exists. '
    'Assess price progress, price repetition and observed flow together. '
    'Past price progress is not progress toward the post-entry target and is never '
    'subtracted from the target. A short or flat prefix alone does not prove failure. '
    'Session return describes this symbol, not the market index. Missing optional '
    'context is unknown, not adverse. No extra confirmation or numeric veto threshold.'
)


def contract():
    return dict(version=VERSION, source_sha256=P.file_hash(__file__),
        dependencies={name:P.file_hash(module.__file__) for name,module in
                      [('causal_prefix', C), ('frozen_risk_role', R), ('union', U),
                       ('compact_runtime', W), ('compact_research', OLD_W)]},
        source_boundary='ORIGINAL_CONFIRMATION_PREFIX_ONLY',
        operating_compatibility='RESEARCH_ONLY_REQUIRES_SEPARATE_IMPLEMENTATION',
        **P.AUTH)


def _checked(value):
    if (not isinstance(value, dict) or value != contract()
            or any(value.get(k) is not v for k,v in P.AUTH.items())):
        raise ValueError('risk_context_contract_changed')


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _snapshot_context(snapshot, logical_input):
    """Copy only exact native branch facts omitted by older input projectors."""
    if snapshot is None:
        return {}, None
    if (not isinstance(snapshot, (list, tuple)) or len(snapshot) != 2
            or not all(isinstance(part, dict) for part in snapshot)):
        raise ValueError('risk_context_snapshot_invalid')
    event, source = snapshot
    common = logical_input['common_context']
    if any(event.get(k) != common.get(k) for k in COMMON_KEYS):
        raise ValueError('risk_context_snapshot_native_conflict')
    branches, inputs = event.get('branch_signals'), source.get('branch_inputs')
    ids = {signal['policy_id'] for signal in logical_input['signals']}
    if (not isinstance(branches, dict) or not isinstance(inputs, dict)
            or set(branches) != ids or set(inputs) != ids):
        raise ValueError('risk_context_snapshot_membership_conflict')
    # Reuse the typed producer: legacy branch events intentionally omit a
    # definition hash, while the union binds their registered definition.
    native = U.production_request(source, U.V1.ARMS[1], event=event)[0]
    if native['signals'] != logical_input['signals']:
        raise ValueError('risk_context_snapshot_projection_conflict')
    result = {}
    for signal in logical_input['signals']:
        branch = branches[signal['policy_id']]
        if (not isinstance(branch, dict)
                or any(branch.get(k) != common.get(k) for k in COMMON_KEYS)
                or U.definition_hash(signal['policy_id']) != signal['definition_sha256']
                or (branch.get('branch_definition_sha256') is not None
                    and branch['branch_definition_sha256'] != signal['definition_sha256'])
                or branch.get('decision_phase') != signal['phase']):
            raise ValueError('risk_context_branch_native_conflict')
        values = branch.get('branch_features')
        if values is None:
            values = {}
        if not isinstance(values, dict):
            raise ValueError('risk_context_branch_features_invalid')
        session = values.get('session')
        if session is not None and not _finite(session):
            raise ValueError('risk_context_session_invalid')
        existing = signal['facts'].get('session_return_pct')
        if existing is not None and existing != session:
            raise ValueError('risk_context_session_conflict')
        anchor_epoch, anchor_price = values.get('session_anchor_epoch'), values.get('session_anchor_price')
        anchor_present = anchor_epoch is not None or anchor_price is not None
        if anchor_present:
            if (not _finite(anchor_epoch) or not 0 < anchor_epoch <= common['epoch']
                    or not _finite(anchor_price) or anchor_price <= 0
                    or session is None
                    or not math.isclose(session, 100*(common['confirmation_price']/anchor_price-1),
                                        rel_tol=1e-10, abs_tol=1e-9)):
                raise ValueError('risk_context_session_anchor_invalid')
        row = dict(symbol_session_return_pct=session)
        for key in ('low_rising', 'high_rising'):
            value = values.get(key)
            if value is not None and type(value) is not bool:
                raise ValueError('risk_context_structure_invalid')
            row[key] = value
        structure = values.get('structure')
        if structure is not None and structure not in {'RISING', 'FALLING', 'MIXED', 'UNKNOWN'}:
            raise ValueError('risk_context_structure_invalid')
        row['observed_structure'] = structure
        result[signal['ref']] = dict(values=row, observation_epoch=common['epoch'],
            session_anchor_verified=True if anchor_present else None)
    return result, P.digest(snapshot)


def project(logical_input, *, expected_contract, source_snapshot=None):
    _checked(expected_contract)
    if (not isinstance(logical_input, dict) or logical_input.get('schema') != U.VERSION
            or not logical_input.get('signals') or VERSION in logical_input):
        raise ValueError('risk_context_input_unsupported')
    W.encode(logical_input)
    common = logical_input.get('common_context') or {}
    if (any(common.get(k) is None for k in COMMON_KEYS)
            or not _finite(common['epoch']) or common['epoch'] <= 0):
        raise ValueError('risk_context_native_identity_missing')
    # Frozen ROLE changes only the fact role. Its implementation and production
    # consumers are untouched, including when the input already has RVP facts.
    result = R.project(logical_input, expected_contract=R.contract('ROLE'))
    extra, snapshot_sha = _snapshot_context(source_snapshot, logical_input)
    setup = result['entry_setup_evidence_v1']
    existing = {fact['id'] for field in ('positive_facts','context_facts','contradicting_facts')
                for fact in setup[field]}
    rows = []
    def add(ref, name, values, risk=None):
        fid = ref + '/' + VERSION + '/' + name
        if fid in existing:
            raise ValueError('risk_context_fact_identity_conflict')
        existing.add(fid)
        setup['context_facts'].append(dict(id=fid, value=values, unit='observed_context'))
        if risk:
            setup['risk_fact_bindings'].setdefault(risk, []).append(fid)
    for signal in result['signals']:
        ref = signal['ref']
        values, coverage = C._features(signal, common)
        geometry, _ = R._path(signal, common)
        prices = signal['recent_observed_prices']
        if prices and prices[-1]['age_sec'] == 0 and prices[-1]['price'] != common['confirmation_price']:
            raise ValueError('risk_context_confirmation_price_conflict')
        observed = len(prices) >= 2 and coverage['observed_span_sec'] > 0
        path = None
        if observed:
            path = dict(observed_return_pct=values['observed_prefix_return_pct'],
                last_from_observed_max_pct=values['observed_prefix_giveback_pct'],
                observed_distinct_price_count=len({p['price'] for p in prices}),
                observation_count=len(prices), observation_span_sec=coverage['observed_span_sec'],
                newest_observation_age_sec=coverage['newest_age_sec'])
            add(ref, 'observed_price_progress', path, 'OBSERVED_PRICE_PATH_CONCERN')
            add(ref, 'observed_path_and_execution_distance', dict(path,
                spread_pct=signal['facts']['spread_pct'],
                target_gap_from_confirmation_trade_pct=geometry['target_gap_from_confirmation_trade_pct'],
                ask_premium_to_confirmation_trade_pct=geometry['ask_premium_to_confirmation_trade_pct'],
                return_60s_minus_spread_pct=values['return_60s_minus_spread_pct']),
                'OBSERVED_EXECUTION_DISTANCE_CONCERN')
            if values['known_side_buy_qty_share_pct'] is not None:
                add(ref, 'observed_flow_and_price_progress', dict(path,
                    known_side_buy_qty_share_pct=values['known_side_buy_qty_share_pct'],
                    known_side_qty_coverage_pct=values['known_side_qty_coverage_pct']),
                    'OBSERVED_FLOW_PATH_CONCERN')
        native_context = extra.get(ref)
        context = native_context['values'] if native_context else None
        if context is None:
            session = signal['facts'].get('session_return_pct')
            if session is not None and not _finite(session):
                raise ValueError('risk_context_session_invalid')
            context = dict(symbol_session_return_pct=session, low_rising=None,
                           high_rising=None, observed_structure=None)
        if any(value is not None and value != 'UNKNOWN' for value in context.values()):
            add(ref, 'observed_symbol_session_and_structure', context, 'OBSERVED_SESSION_CONTEXT_CONCERN')
        rows.append(dict(signal_ref=ref, source_signal_sha256=P.digest(signal),
            prefix_coverage=coverage, price_path_observed=observed,
            snapshot_context_available=ref in extra,
            snapshot_observation_epoch=native_context['observation_epoch'] if native_context else None,
            session_anchor_verified=native_context['session_anchor_verified'] if native_context else None))
    if not any(setup['risk_fact_bindings'].values()):
        # Do not silently construct another PASS-only evaluation. No observation
        # is fabricated to fill the vocabulary: the experiment excludes this row.
        raise ValueError('risk_context_no_citable_observations')
    result[VERSION] = dict(original_logical_input_sha256=P.digest(logical_input),
        source_snapshot_sha256=snapshot_sha, per_signal=rows, interpretation=INTERPRETATION,
        risk_bindings_are_vocabulary_only=True, contract=expected_contract)
    W.encode(result)
    return result


def validate_projected(original, projected, *, expected_contract, source_snapshot=None):
    if projected != project(original, expected_contract=expected_contract, source_snapshot=source_snapshot):
        raise ValueError('risk_context_projection_changed')
    return projected


def transform_request(req, logical_input, *, expected_contract, source_snapshot=None):
    """Transform one exact request; caller owns frozen membership and budget."""
    if any(req.get(k) is not v for k,v in P.AUTH.items()):
        raise ValueError('risk_context_request_authority_invalid')
    transformed = project(logical_input, expected_contract=expected_contract, source_snapshot=source_snapshot)
    result = copy.deepcopy(req)
    candidate = result['candidate']
    present = [(field,codec) for field,codec in
               [('compact_runtime_contract',W),('compact_wire_contract',OLD_W)] if candidate.get(field)]
    if len(present) > 1:
        raise ValueError('risk_context_multiple_wire_contracts')
    codec = present[0][1] if present else None
    if codec:
        field = present[0][0]
        wire, schema, aliases = codec.encode(logical_input)
        if (candidate[field] != codec.contract() or req.get('candidate_input') != wire
                or candidate.get('logical_input_sha256') != P.digest(logical_input)
                or candidate.get('response_schema') != schema
                or candidate.get('citation_map_sha256') != P.digest(aliases)
                or not candidate['system_prompt'].endswith(codec.SUFFIX)):
            raise ValueError('risk_context_original_request_changed')
        candidate['system_prompt'] = candidate['system_prompt'][:-len(codec.SUFFIX)]
        for key in (field,'logical_input_sha256','citation_map_sha256'):
            candidate.pop(key,None)
    elif req.get('candidate_input') != logical_input or candidate.get('response_schema') != U.response_schema(logical_input):
        raise ValueError('risk_context_original_request_changed')
    if 'candidate_input_sha256' in req and req['candidate_input_sha256'] != P.digest(req['candidate_input']):
        raise ValueError('risk_context_original_request_changed')
    for key in ('response_schema_sha256','response_schema_instance_sha256'):
        if key in req['candidate'] and req['candidate'][key] != P.digest(req['candidate']['response_schema']):
            raise ValueError('risk_context_original_request_changed')
    schema = U.response_schema(transformed)
    result.update(candidate_input=transformed, candidate_input_sha256=P.digest(transformed))
    candidate.update(response_schema=schema, response_schema_sha256=P.digest(schema),
        response_schema_instance_sha256=P.digest(schema), schema_name=U.VERSION,
        offline_risk_context_contract=expected_contract,
        original_logical_input_sha256=P.digest(logical_input))
    candidate.pop('contract_sha256',None)
    result['paired_replay_id'] = P.digest([req['paired_replay_id'], VERSION, expected_contract,
        {k:result[k] for k in ('candidate_input','candidate','control','stage')}])
    return codec.request(result, transformed, codec.contract()) if codec else result


def seal_evaluation(report, *, expected_contract):
    """Use the native publisher's existing development rejection boundary."""
    _checked(expected_contract)
    if not isinstance(report, dict) or any(
            k in report and report[k] is not v for k,v in P.AUTH.items()):
        raise ValueError('risk_context_evaluation_authority_invalid')
    result = copy.deepcopy(report)
    research = result.get('research', {})
    if not isinstance(research, dict):
        raise ValueError('risk_context_evaluation_research_invalid')
    result.update(research=dict(research,purpose='development'),
        offline_input_experiment=expected_contract,
        operating_compatibility='requires_separate_input_implementation', **P.AUTH)
    return P.seal(result)
