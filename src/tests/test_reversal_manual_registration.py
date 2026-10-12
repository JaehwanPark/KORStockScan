"""Native FIRST hold/breakout and explicit residual ADD contracts."""
import copy
import json
import pytest
from src.engine.scalping import reversal_extended_catalog as C
from src.engine.scalping import reversal_extended_state as R
from src.engine.scalping import reversal_extended_auxiliary as A
from src.engine.scalping import reversal_extended_union as U
from src.engine.scalping import reversal_manual_registration as M
from src.engine.scalping import continuous_reversal_postclose as P
from src.tests.test_reversal_path_policy import row


def bid_for(group, root, market='PRE', band='LT_20000'):
    return next(b for b,d in C.ADDITIONAL_DEFINITIONS.items() if
        (d['symbol_group'],d['market'],d['price_band'],d['root_confirmation'])==(group,market,band,root))


def observe(state, rows, *, symbol='000001',venue='NXT',session='NXT_PREMARKET'):
    found=[]
    for tick in rows:
        tick[9]=symbol+('_NX' if venue=='NXT' else '_AL')
        result=state.observe(tick,symbol=symbol,venue=venue,session=session)
        if result:found.extend(copy.deepcopy(result))
    return found


def hold_rows():
    return [row(0,100)]+[row(i,99.5) for i in range(1,121)]+[
        row(121,99.49),row(122,99.5),row(123,99.5001),row(124,99.5001),row(125,99.5001)]


def test_frozen_base_registry_is_unchanged_and_six_additions_have_four_scopes():
    assert len(C.NEW_DEFINITIONS)==13 and len(C.ADDITIONAL_DEFINITIONS)==6
    assert C.SHA256==P.digest(C.MANIFEST)
    assert C.registry_for(C.NEW_DEFINITIONS)==C.SHA256
    assert C.registry_for(C.ADDITIONAL_DEFINITIONS)==C.SUCCESSOR_SHA256
    assert len(M.approved_scopes())==4
    for b,d in C.ADDITIONAL_DEFINITIONS.items():
        assert b=='manual_residual_'+P.digest(d)[:16]
        sid='|'.join((d['symbol_group'],d['market'],d['price_band']))
        assert C.applicable(b,sid,d['route'])
        assert not C.applicable(b,sid,'SOR' if d['route']=='NXT' else 'NXT')


@pytest.mark.parametrize('root,confirmation', [('FIRST_HOLD1',123),('FIRST_HOLD3',125)])
def test_hold_confirms_first_actual_received_tick_with_original_anchor(root,confirmation):
    bid=bid_for('other_non_fixed',root)
    values=hold_rows()
    state=R.State(branch_ids=[bid],session_anchor=values[0])
    hits=observe(state,values)
    assert len(hits)==1
    event=hits[0]['event'];signal=event['branch_signals'][bid]
    assert signal['epoch']==row(confirmation,99.5)[0]
    assert signal['signal_proof']['epoch']==row(122,99.5)[0]
    assert signal['decision_phase']=='FIRST_PRICE_HOLD'
    A.validate_signal(signal)
    inp,prompt,schema=U.production_request(dict(branch_inputs=hits[0]['path_inputs']),U.V1.ARMS[1],event=event)
    assert len(inp['signals'])==1 and prompt.isascii()
    assert inp['signals'][0]['observed_signal']['root_contract']['hold_seconds']==int(root[-1])


@pytest.mark.parametrize('case', ['breach','epoch','sequence','invalid','missing_quote'])
def test_hold_never_stitches_or_reconfirms_failed_first_tick(case):
    bid=bid_for('other_non_fixed','FIRST_HOLD3');values=hold_rows()
    if case=='breach':values[-3][3]=99.49
    if case=='epoch':values[-3][1]+=1
    if case=='sequence':values[-3][2]+=100
    if case=='invalid':values[-3][8]=0
    if case=='missing_quote':values[-1][5]=None
    hits=observe(R.State(branch_ids=[bid],session_anchor=values[0]),values)
    assert not hits


def test_same_tick_two_hold_branches_are_one_canonical_opportunity():
    one=bid_for('other_non_fixed','FIRST_HOLD1');three=bid_for('other_non_fixed','FIRST_HOLD3')
    values=hold_rows()[:-3]+[row(125,99.5001)]
    values[-1][2]=values[-2][2]+1
    hits=observe(R.State(branch_ids=[one,three],session_anchor=values[0]),values)
    assert len(hits)==1 and set(hits[0]['event']['branch_signals'])=={one,three}
    inp,_,_=U.production_request(dict(branch_inputs=hits[0]['path_inputs']),U.V1.ARMS[1],event=hits[0]['event'])
    assert len(inp['signals'])==2
    assert inp['common_context']['opportunity_key']==U.opportunity(hits[0]['event'])


def test_breakout_requires_known_false_transition_and_structural_prefix():
    bid=bid_for('other_non_fixed','BREAKOUT60',band='GE_100000')
    values=[row(i,200000 if i<30 else 200100) for i in range(61)]+[row(61,200200)]
    hits=observe(R.State(branch_ids=[bid]),values)
    assert len(hits)==1
    signal=hits[0]['event']['branch_signals'][bid]
    assert signal['signal_proof']['previous_condition'] is False
    assert signal['decision_phase']=='HIGH_BREAKOUT'
    A.validate_signal(signal)
    bad=copy.deepcopy(signal);bad['signal_proof']['previous_condition']=None
    with pytest.raises(ValueError,match='proof_invalid'):A.validate_signal(bad)


def request(tmp_path):
    evidence=tmp_path/'evidence.json';evidence.write_text('{}\n')
    return P.seal(dict(schema='main_residual_registration_request_v1',kind='ADD',
        operator_receipt=M.AUTHORITY,research_batch_sha256=M.PROPOSAL_SHA256,
        registry_sha256=C.SUCCESSOR_SHA256,scopes=M.approved_scopes(),
        definition_hashes={b:P.digest(d) for b,d in C.ADDITIONAL_DEFINITIONS.items()},
        comparison_result_required=False,source_receipts=[dict(path=str(evidence),sha256=P.file_hash(evidence))]))


@pytest.mark.parametrize('field', ['operator_receipt','research_batch_sha256','registry_sha256','scopes','definition_hashes'])
def test_registration_rejects_modified_authority_source_or_membership(tmp_path,field):
    original=request(tmp_path);M.validate_request(original)
    wrong=copy.deepcopy(original);wrong[field]={} if isinstance(wrong[field],dict) else 'changed'
    with pytest.raises(ValueError,match='authority_or_definition'):M.validate_request(P.seal(wrong))


def test_registration_keeps_source_gap_and_rejects_tampered_frozen_input(tmp_path):
    value=request(tmp_path);M.validate_request(value)
    (tmp_path/'evidence.json').write_text('changed')
    with pytest.raises(ValueError,match='evidence_changed'):M.validate_request(value)


def test_native_machine_registration_emits_compatibility_terminal_without_legacy_selection_field(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import reversal_extended_registration as ER
    request=dict(publication_date='2026-10-12',target_date='2026-10-13',research_batch_sha256='b'*64,
                 original_reports={'machine-comparison':{'path':'original'}})
    parent=dict(bundle_sha256='p')
    original=P.seal(dict(parent_bundle_sha256='p',source_receipts=[],cells=[],
        selection_metric='cumulative_raw_win_fraction',status='completed'))
    storage={'original':original};writes=[]
    monkeypatch.setattr(M,'validate_request',lambda r:r)
    monkeypatch.setattr(M.N,'_read',lambda p:storage.get(str(p),request))
    monkeypatch.setattr(M,'load_offline_parent',lambda *a:parent)
    change=dict(request,source_receipts=[])
    monkeypatch.setattr(M,'pending',lambda *a:change)
    monkeypatch.setattr(V,'detector_manifest',lambda *a,**k:{'detector_manifest_hash':'manifest'})
    monkeypatch.setattr(V,'contract_modules',lambda:(SimpleNamespace(__file__=__file__),))
    def write(path,body):storage[str(path)]=body;writes.append((path,body))
    monkeypatch.setattr(P,'write',write)
    def typed(data,day,pub,parent,machine,**kwargs):
        P.write(Path(kwargs['output_directory'])/'machine.json',P.seal(machine))
    from pathlib import Path
    monkeypatch.setattr(ER,'initial_reports',typed)
    result=M.run_postclose(tmp_path,'2026-10-12','2026-10-12','machine')
    assert result['selection_basis']=='cumulative_raw_win_fraction'
    terminal=next(body for path,body in writes if path.name=='winrate_policy_terminal_2026-10-12.json')
    assert terminal['status']=='completed' and terminal['staged']['status']=='machine_component_prepared'
    assert terminal['report_sha256']==result['artifact_content_sha256']
