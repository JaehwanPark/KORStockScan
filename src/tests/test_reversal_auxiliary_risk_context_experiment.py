"""Research risk vocabulary remains observed, exact and outside live adoption."""
import copy
import hashlib
from pathlib import Path

import pytest

from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import reversal_auxiliary_risk_context_experiment as X
from src.engine.scalping import reversal_auxiliary_risk_role_experiment as R
from src.engine.scalping import reversal_auxiliary_production_input as LIVE
from src.engine.scalping import reversal_auxiliary_wire as W
from src.engine.scalping import reversal_auxiliary_research_wire as OLD_W
from src.engine.scalping import reversal_auxiliary_registry as G
from src.engine.scalping import reversal_extended_union as U
from src.tests.test_reversal_auxiliary_risk_role_experiment import source, legacy
from src.tests.test_reversal_auxiliary_causal_experiment import request
from src.tests.test_reversal_extended_policy import FIXTURES


def empty_vocabulary():
    logical, registry = legacy(0.)
    setup = logical['entry_setup_evidence_v1']
    setup.update(context_facts=[], contradicting_facts=[], risk_fact_bindings={})
    for signal in logical['signals']:
        signal['facts'].pop('session_return_pct', None)
    return logical, registry


def wire_response(logical, risk, fact, verdict='CAUTION'):
    aliases = W.encode(logical)[2]
    return dict(assessed={aliases[s['ref']]:True for s in logical['signals']},
                screen=dict(verdict=verdict, risk=risk, fact=aliases[fact]), confidence=50)


def test_frozen_production_transform_sha_and_original_fields_remain_unchanged():
    assert hashlib.sha256(Path(R.__file__).read_bytes()).hexdigest() == LIVE.REVIEWED_TRANSFORM_SHA256
    logical,_ = source()
    before = copy.deepcopy(logical)
    projected = X.project(logical, expected_contract=X.contract())
    assert logical == before
    for field in ('signals','common_context','observation_phase'):
        assert projected[field] == before[field]
    assert projected['entry_setup_evidence_v1']['positive_facts'] == before['entry_setup_evidence_v1']['positive_facts']
    for risk, ids in before['entry_setup_evidence_v1']['risk_fact_bindings'].items():
        assert projected['entry_setup_evidence_v1']['risk_fact_bindings'][risk] == ids
    assert not any(f['id'].endswith('/observed_spread') for f in projected['entry_setup_evidence_v1']['contradicting_facts'])
    assert X.validate_projected(logical, projected, expected_contract=X.contract()) == projected


def test_empty_original_vocabulary_can_express_only_bound_observed_risks():
    logical,registry = empty_vocabulary()
    assert W.encode(logical)[1]['properties']['screen']['anyOf'][0]['properties']['verdict']['enum'] == ['PASS']
    projected = X.project(logical, expected_contract=X.contract())
    risk = 'OBSERVED_PRICE_PATH_CONCERN'
    fact = projected['entry_setup_evidence_v1']['risk_fact_bindings'][risk][0]
    for verdict in ('CAUTION','VETO'):
        decoded = W.decode(wire_response(projected,risk,fact,verdict),projected,registry['base_arm'])
        assert decoded['contradicting_fact_ids'] == [fact]
        assert decoded['risk_verdict'] == verdict
    with pytest.raises(ValueError,match='union_nonpass_risk_unbound'):
        W.decode(wire_response(projected,risk,'observed_machine_signal'),projected,registry['base_arm'])
    with pytest.raises(ValueError,match='union_nonpass_risk_unbound'):
        W.decode(wire_response(projected,'INVENTED_FUTURE_LOSS',fact),projected,registry['base_arm'])
    passed = W.decode(wire_response(projected,'NO_BLOCKING_RISK','observed_machine_signal','PASS'),projected,registry['base_arm'])
    assert passed['risk_verdict'] == 'PASS'


@pytest.mark.parametrize('codec',[None,W,OLD_W])
def test_exact_request_transform_preserves_prompt_model_and_is_separately_identified(codec):
    logical,_ = source()
    logical = R.project(logical, expected_contract=R.contract('ROLE_VOCAB_PATH'))
    req = request(logical)
    if codec:
        req = codec.request(req,logical,codec.contract())
    before = copy.deepcopy((req,logical))
    actual = X.transform_request(req, logical, expected_contract=X.contract())
    projected = X.project(logical,expected_contract=X.contract())
    assert actual['candidate_input'] == (codec.encode(projected)[0] if codec else projected)
    assert actual['candidate']['system_prompt'] == req['candidate']['system_prompt']
    assert actual['control'] == req['control']
    for field in ('model','max_output_tokens','reasoning_effort'):
        assert actual['candidate'][field] == req['candidate'][field]
    assert actual['candidate']['offline_risk_context_contract'] == X.contract()
    assert actual['paired_replay_id'] != req['paired_replay_id']
    assert actual['allowed_runtime_apply'] is False and actual['actual_order_submitted'] is False
    assert (req,logical) == before
    assert X.transform_request(req,logical,expected_contract=X.contract()) == actual


@pytest.mark.parametrize('change',[
    lambda s:s['recent_observed_prices'][0].update(age_sec=-1),
    lambda s:s['recent_observed_prices'][1].update(age_sec=3),
    lambda s:s['recent_observed_prices'][0].update(price=float('nan')),
    lambda s:s['recent_observed_prices'][0].update(qty=-1),
    lambda s:s['recent_observed_prices'][0].update(side='LATER_BUY'),
    lambda s:s['recent_observed_prices'][-1].update(price=1),
    lambda s:s['facts'].update(entry_ask=1),
    lambda s:s['facts'].update(session_return_pct=float('inf')),
])
def test_corrupt_or_conflicting_observations_are_excluded(change):
    logical,_ = source()
    change(logical['signals'][0])
    with pytest.raises(ValueError):
        X.project(logical, expected_contract=X.contract())


def test_missing_or_single_clock_prefix_does_not_invent_progress_or_risk():
    logical,_ = empty_vocabulary()
    for signal in logical['signals']:
        signal['recent_observed_prices'] = []
    with pytest.raises(ValueError,match='risk_context_no_citable_observations'):
        X.project(logical,expected_contract=X.contract())
    for signal in logical['signals']:
        price=signal['facts']['confirmation_price']
        signal['recent_observed_prices']=[dict(age_sec=0,price=price,qty=None,side='UNKNOWN')]*2
    with pytest.raises(ValueError,match='risk_context_no_citable_observations'):
        X.project(logical,expected_contract=X.contract())


def test_optional_quantity_unknown_is_not_zero_or_false_flow():
    logical,_ = empty_vocabulary()
    for signal in logical['signals']:
        for row in signal['recent_observed_prices']:
            row['qty']=None
    projected=X.project(logical,expected_contract=X.contract())
    assert 'OBSERVED_FLOW_PATH_CONCERN' not in projected['entry_setup_evidence_v1']['risk_fact_bindings']
    row=projected[X.VERSION]['per_signal'][0]
    assert row['prefix_coverage']['complete_quantity_observation'] is False
    assert 'OBSERVED_PRICE_PATH_CONCERN' in projected['entry_setup_evidence_v1']['risk_fact_bindings']


def snapshot_source():
    fixture=next(iter(FIXTURES.values()))
    snapshot=copy.deepcopy([fixture['event'],fixture['source']])
    registry=G.definition(U.V1.ARMS[1],input_version=U.VERSION)
    logical=G.production_request(snapshot,registry)[0]
    return logical,snapshot


def test_exact_snapshot_supplies_only_available_symbol_context():
    logical,snapshot=snapshot_source()
    before=copy.deepcopy((logical,snapshot))
    projected=X.project(logical,expected_contract=X.contract(),source_snapshot=snapshot)
    setup=projected['entry_setup_evidence_v1']
    ids=setup['risk_fact_bindings']['OBSERVED_SESSION_CONTEXT_CONCERN']
    context=next(f['value'] for f in setup['context_facts'] if f['id']==ids[0])
    branch=next(iter(snapshot[0]['branch_signals'].values()))
    assert context['symbol_session_return_pct']==branch['branch_features']['session']
    assert context['low_rising'] is branch['branch_features']['low_rising']
    assert context['high_rising'] is branch['branch_features']['high_rising']
    assert projected[X.VERSION]['source_snapshot_sha256']==P.digest(snapshot)
    assert (logical,snapshot)==before


@pytest.mark.parametrize('change',[
    lambda snapshot:snapshot[0].update(native_sequence=1),
    lambda snapshot:next(iter(snapshot[0]['branch_signals'].values())).update(native_epoch=1),
    lambda snapshot:next(iter(snapshot[0]['branch_signals'].values())).update(branch_definition_sha256='0'*64),
    lambda snapshot:next(iter(snapshot[0]['branch_signals'].values()))['branch_features'].update(session=999),
    lambda snapshot:next(iter(snapshot[0]['branch_signals'].values()))['branch_features'].update(session_anchor_epoch=9e12),
    lambda snapshot:next(iter(snapshot[0]['branch_signals'].values()))['branch_features'].update(low_rising='False'),
    lambda snapshot:next(iter(snapshot[0]['branch_signals'].values())).update(branch_features=[]),
])
def test_snapshot_identity_and_source_contract_cannot_be_substituted(change):
    logical,snapshot=snapshot_source()
    change(snapshot)
    with pytest.raises(ValueError):
        X.project(logical,expected_contract=X.contract(),source_snapshot=snapshot)


def test_missing_optional_anchor_is_unknown_but_partial_anchor_is_invalid():
    logical,snapshot=snapshot_source()
    for branch in snapshot[0]['branch_signals'].values():
        branch['branch_features'].pop('session_anchor_epoch',None)
        branch['branch_features'].pop('session_anchor_price',None)
    projected=X.project(logical,expected_contract=X.contract(),source_snapshot=snapshot)
    assert all(row['session_anchor_verified'] is None for row in projected[X.VERSION]['per_signal'])
    assert all(row['snapshot_observation_epoch']==logical['common_context']['epoch']
               for row in projected[X.VERSION]['per_signal'])
    next(iter(snapshot[0]['branch_signals'].values()))['branch_features']['session_anchor_price']=100.
    with pytest.raises(ValueError,match='risk_context_session_anchor_invalid'):
        X.project(logical,expected_contract=X.contract(),source_snapshot=snapshot)


def test_research_evaluation_hits_native_publisher_rejection_before_any_recompute(tmp_path,monkeypatch):
    from datetime import datetime
    from src.engine.scalping import reversal_auxiliary_intraday as I
    from src.engine.scalping import reversal_auxiliary_tuning as T
    report=X.seal_evaluation(dict(schema='risk_context_test',research={'experiment':'test'},
        source_date='2026-10-16'),expected_contract=X.contract())
    assert report['offline_input_experiment']==X.contract()
    assert report['operating_compatibility']=='requires_separate_input_implementation'
    assert all(report[k] is v for k,v in P.AUTH.items())
    path=tmp_path/'evaluation.json'
    P.write(path,report)
    def forbidden(*args,**kwargs):
        pytest.fail('offline experiment reached native recomputation or publication')
    monkeypatch.setattr(T,'evaluate',forbidden)
    monkeypatch.setattr(I,'publisher_locks',forbidden)
    with pytest.raises(ValueError,match='auxiliary_development_evaluation_not_publishable'):
        I.publish(tmp_path,path,expected_parent=None,confirm=I.AUTHORITY,
                  now=datetime(2026,10,17,12,tzinfo=I.K.KST))
    with pytest.raises(ValueError,match='risk_context_evaluation_authority_invalid'):
        X.seal_evaluation(dict(report,allowed_runtime_apply=True),expected_contract=X.contract())


def test_request_without_explicit_offline_authority_cannot_be_transformed():
    logical,_=source()
    req=request(logical)
    req.pop('broker_order_forbidden')
    with pytest.raises(ValueError,match='risk_context_request_authority_invalid'):
        X.transform_request(req,logical,expected_contract=X.contract())


def test_projection_and_contract_tampering_are_rejected():
    logical,_=source()
    projected=X.project(logical,expected_contract=X.contract())
    projected['entry_setup_evidence_v1']['context_facts'][-1]['value']['symbol_session_return_pct']=999
    with pytest.raises(ValueError,match='risk_context_projection_changed'):
        X.validate_projected(logical,projected,expected_contract=X.contract())
    with pytest.raises(ValueError,match='risk_context_contract_changed'):
        X.project(logical,expected_contract=dict(X.contract(),allowed_runtime_apply=True))
    original=X.project(logical,expected_contract=X.contract())
    with pytest.raises(ValueError,match='risk_context_input_unsupported'):
        X.project(original,expected_contract=X.contract())


@pytest.mark.parametrize('field',['candidate_input_sha256','response_schema_sha256','logical_input_sha256'])
def test_request_digest_tampering_cannot_enter_experiment(field):
    logical,_=source()
    req=W.request(request(logical),logical,W.contract())
    (req if field=='candidate_input_sha256' else req['candidate'])[field]='0'*64
    with pytest.raises(ValueError,match='risk_context_original_request_changed'):
        X.transform_request(req,logical,expected_contract=X.contract())
