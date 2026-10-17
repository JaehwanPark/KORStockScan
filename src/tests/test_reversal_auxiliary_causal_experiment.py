"""Causal input ablation stays offline, immutable and strictly source-bound."""
import copy

import pytest

from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import reversal_auxiliary_causal_experiment as E
from src.engine.scalping import reversal_auxiliary_registry as G
from src.engine.scalping import reversal_auxiliary_research_wire as OLD_W
from src.engine.scalping import reversal_auxiliary_wire as W
from src.engine.scalping import reversal_extended_union as U
from src.tests.test_reversal_extended_policy import FIXTURES


def source():
    fixture = next(iter(FIXTURES.values()))
    old = G.definition(U.V1.ARMS[1], input_version=U.VERSION)
    snap = (fixture['event'], fixture['source'])
    logical = G.production_request(snap, old)[0]
    for signal in logical['signals']:
        signal['recent_observed_prices'] = [
            dict(age_sec=2., price=100., qty=5., side='SELL'),
            dict(age_sec=1., price=102., qty=10., side='BUY'),
            dict(age_sec=0., price=101., qty=5., side='UNKNOWN')]
        signal['facts'].update(return_60s_pct=.3, spread_pct=.2)
    return logical, old


def request(logical):
    return dict(paired_replay_id='parent-request', candidate_input=copy.deepcopy(logical),
        control=dict(provider='openai', model='gpt-5.4-nano'), stage='entry',
        candidate=dict(system_prompt='Frozen prompt.', model='gpt-5.4-nano',
            max_output_tokens=1024, reasoning_effort='none',
            response_schema=U.response_schema(logical)), **P.AUTH)


def test_causal_campaign_validates_actual_wire_response_and_cannot_publish(tmp_path, monkeypatch):
    from datetime import datetime
    from src.engine.ai import offline_comparison_store as S
    from src.engine.scalping import reversal_auxiliary_intraday as I
    from src.engine.scalping import reversal_auxiliary_research as Q
    from src.engine.scalping import reversal_auxiliary_tuning as T
    from src.tests.test_offline_comparison_store import activate
    fixture = FIXTURES['manual_extended_f9a43c88911fdc0b']
    snapshot = [fixture['event'], fixture['source']]
    sid = 'samsung|PRE|ALL|NXT'
    original = G.definition(U.V1.ARMS[1], input_version=U.VERSION)
    candidate = G.definition(U.V1.ARMS[1], input_version=U.VERSION,
        prompt=original['prompt'] + '\nConsider the explicitly supplied prefix coverage.\n')
    for registry in (original, candidate):
        G.register(tmp_path, registry)
    current = G.compact_definition(original, research_wire_contract=OLD_W.contract())
    candidate = G.compact_definition(candidate, research_wire_contract=OLD_W.contract())
    for registry in (current, candidate):
        G.register(tmp_path, registry)
    before = copy.deepcopy((snapshot, current, candidate))
    manifest = dict(scopes={sid:list(fixture['event']['branch_signals'])},
        detector_manifest_hash='a' * 64)
    parent = dict(bundle_sha256='b' * 64, continuous_reversal=dict(
        schema='continuous_reversal_policy_v6', operating_manifest=manifest))
    with S.Store(tmp_path) as store:
        activate(store)
        points = [dict(opportunity_key=U.opportunity(fixture['event']), scope=sid,
            symbol=fixture['event']['symbol'], day='2026-10-07', outcome={'status':'WIN'},
            snapshot_obj=store.put(snapshot))]
        part = dict(records_object=store.put(points), records_sha256=P.digest(points))
    machine = P.seal(dict(source_date='2026-10-07', policy_schema='continuous_reversal_policy_v6',
        operating_manifest=manifest, partitions=[part]))
    monkeypatch.setattr(Q, 'current_bindings', lambda *a:{sid:current['registry_sha256']})
    Q.authorize(tmp_path, confirm=Q.AUTHORITY, source_dates=['2026-10-07'],
        approval_reference='User: isolated research fixture')
    Q.configure(tmp_path, experiment='causal-wire', candidate=candidate['registry_sha256'],
        scopes=[sid], seed='fixed', max_pairs=1, causal_prefix=True)
    campaign = T.prepare(tmp_path, '2026-10-07', machine, parent, research='causal-wire')
    campaign_path = Q.directory(tmp_path, 'causal-wire') / 'campaigns' / (
        campaign['artifact_content_sha256'] + '.json')
    sent = []
    def transport(req, timeout_sec):
        wire = req['candidate_input']
        # Cite a fact that exists only in the enriched input. Decoding with the
        # original logical input would reject both its map and response IDs.
        fact = next(f for f in wire['entry_setup_evidence_v1']['context_facts']
            if f.get('citation_name') == 'observed_prefix_return_pct')
        sent.append(req['paired_replay_id'])
        return dict(provider_provenance=dict(response_id='fixture-' + req['paired_replay_id']),
            candidate_response=dict(assessed={s['ref']:True for s in wire['signals']},
                screen=dict(verdict='CAUTION', risk='PREFIX_PATH_CONCERN', fact=fact['id']),
                confidence=50))
    calls = T.calls(tmp_path, '2026-10-07', campaign_path=campaign_path, transport=transport)
    assert calls['new_calls'] == 2 and len(set(sent)) == 2
    with S.Store(tmp_path, readonly=True) as store:
        for role, rid in campaign['pairs'][0]['requests'].items():
            state, obj = store.db.execute('SELECT state,result_obj FROM requests WHERE id=?', (rid,)).fetchone()
            assert state == 'completed'
            assert store.get(obj)['validation_errors'] == []
            req = store.request(rid)
            definition = current if role == 'current' else candidate
            assert req == T.expected_request(tmp_path, campaign, campaign['pairs'][0], role,
                snapshot, definition)
            assert req['candidate_input'] != G.request(snapshot, definition)['candidate_input']
    evaluated = T.evaluate(tmp_path, '2026-10-07', campaign_path=campaign_path)
    assert evaluated['scopes'][sid]['paired_points'] == 1
    assert evaluated['comparison_complete'] is True
    assert evaluated['operating_compatibility'] == 'requires_separate_input_implementation'
    assert evaluated['offline_input_experiment'] == E.contract()
    assert T.prepare(tmp_path, '2026-10-07', machine, parent, research='causal-wire') == campaign
    evaluation_path = Q.directory(tmp_path, 'causal-wire') / 'evaluations' / (
        evaluated['artifact_content_sha256'] + '.json')
    with pytest.raises(ValueError, match='research_native_comparison_required'):
        I.publish(tmp_path, evaluation_path, expected_parent=None, confirm=I.AUTHORITY,
            now=datetime(2026, 10, 8, 10, tzinfo=I.K.KST))
    assert (snapshot, current, candidate) == before


def test_exact_prefix_arithmetic_original_immutable_and_bound_facts():
    original, registry = source()
    before = copy.deepcopy(original)
    enriched = E.project(original)
    assert original == before
    assert {k:v for k,v in enriched.items() if k not in {'causal_prefix_evidence', 'entry_setup_evidence_v1'}} == {
        k:v for k,v in original.items() if k != 'entry_setup_evidence_v1'}
    row = enriched['causal_prefix_evidence']['per_signal'][0]
    assert row['values']['observed_prefix_return_pct'] == pytest.approx(1)
    assert row['values']['observed_prefix_giveback_pct'] == pytest.approx(100*(101/102-1))
    assert row['values']['known_side_buy_qty_share_pct'] == pytest.approx(100*10/15)
    assert row['values']['known_side_qty_coverage_pct'] == 75
    assert row['values']['return_60s_minus_spread_pct'] == pytest.approx(.1)
    assert row['coverage']['observed_span_sec'] == 2
    assert row['source_signal_sha256'] == P.digest(original['signals'][0])
    assert E.validate_projected(original, enriched) == enriched
    wire, _, aliases = W.encode(enriched)
    fid = next(f['id'] for f in enriched['entry_setup_evidence_v1']['context_facts']
               if f['id'].endswith('/observed_prefix_giveback_pct'))
    raw = dict(assessed={aliases[s['ref']]:True for s in enriched['signals']},
        screen=dict(verdict='CAUTION', risk='PREFIX_PATH_CONCERN', fact=aliases[fid]), confidence=51)
    decoded = W.decode(raw, enriched, registry['base_arm'])
    assert U.validate_response(decoded, enriched, arm=registry['base_arm']) == []
    assert wire != original
    mutated = copy.deepcopy(enriched)
    mutated['causal_prefix_evidence']['per_signal'][0]['values']['observed_prefix_return_pct'] = 999
    with pytest.raises(ValueError, match='evidence_changed'):
        E.validate_projected(original, mutated)


@pytest.mark.parametrize('defect', ['future', 'order', 'nan_price', 'negative_qty', 'unknown_side'])
def test_malformed_or_future_observation_is_never_repaired(defect):
    original, _ = source()
    prices = original['signals'][0]['recent_observed_prices']
    if defect == 'future': prices[-1]['age_sec'] = -.01
    if defect == 'order': prices[-1]['age_sec'] = 4
    if defect == 'nan_price': prices[-1]['price'] = float('nan')
    if defect == 'negative_qty': prices[-1]['qty'] = -1
    if defect == 'unknown_side': prices[-1]['side'] = 'invented'
    with pytest.raises(ValueError, match='source_invalid'):
        E.project(original)


def test_missing_and_incomplete_prefix_remain_unknown_not_zero():
    original, _ = source()
    original['signals'][0]['recent_observed_prices'] = []
    original['signals'][0]['facts']['return_60s_pct'] = None
    row = E.project(original)['causal_prefix_evidence']['per_signal'][0]
    assert all(v is None for k,v in row['values'].items() if k!='root_to_confirmation_return_pct')
    assert row['coverage']['observations'] == 0
    original, _ = source()
    original['signals'][0]['recent_observed_prices'][0]['qty'] = None
    row = E.project(original)['causal_prefix_evidence']['per_signal'][0]
    assert row['values']['known_side_qty_coverage_pct'] is None
    assert row['coverage']['complete_quantity_observation'] is False


@pytest.mark.parametrize('codec', [None, W, OLD_W])
def test_request_transform_preserves_wire_transport_and_immutable_registry(codec):
    logical, registry = source()
    req = request(logical)
    if codec: req = codec.request(req, logical, codec.contract())
    before = copy.deepcopy((req, logical, registry))
    enriched = E.project(logical)
    transformed = E.transform_request(req, logical, contract=E.contract())
    assert (req, logical, registry) == before
    assert transformed['paired_replay_id'] != req['paired_replay_id']
    assert E.transform_request(req, logical, contract=E.contract()) == transformed
    assert transformed['control'] == req['control']
    for k in ('model', 'max_output_tokens', 'reasoning_effort'):
        assert transformed['candidate'][k] == req['candidate'][k]
    assert transformed['candidate']['offline_causal_prefix_contract'] == E.contract()
    assert transformed['candidate']['original_logical_input_sha256'] == P.digest(logical)
    if codec:
        assert transformed['candidate_input'] == codec.encode(enriched)[0]
        assert transformed['candidate']['system_prompt'] == req['candidate']['system_prompt']
        assert transformed['candidate']['system_prompt'].count(codec.SUFFIX) == 1
        assert transformed['candidate']['logical_input_sha256'] == P.digest(enriched)
    else:
        assert transformed['candidate_input'] == enriched
    assert transformed['candidate']['response_schema_sha256'] == P.digest(transformed['candidate']['response_schema'])


def test_tampered_parent_request_or_experiment_contract_rejected():
    logical, _ = source()
    req = W.request(request(logical), logical, W.contract())
    bad = copy.deepcopy(E.contract()); bad['runtime_effect'] = True
    with pytest.raises(ValueError, match='contract_changed'):
        E.transform_request(req, logical, contract=bad)
    req['candidate']['logical_input_sha256'] = 'f'*64
    with pytest.raises(ValueError, match='original_request_changed'):
        E.transform_request(req, logical, contract=E.contract())


@pytest.mark.parametrize('field', ['response_schema', 'citation_map_sha256', 'candidate_input_sha256'])
def test_original_wire_contract_corruption_is_not_silently_reencoded(field):
    logical, _ = source()
    req = W.request(request(logical), logical, W.contract())
    if field == 'candidate_input_sha256': req[field] = 'f'*64
    elif field == 'response_schema': req['candidate'][field] = {}
    else: req['candidate'][field] = 'f'*64
    with pytest.raises(ValueError, match='original_request_changed'):
        E.transform_request(req, logical, contract=E.contract())


def test_finite_inputs_whose_derived_values_overflow_are_rejected():
    logical, _ = source()
    prices = logical['signals'][0]['recent_observed_prices']
    prices[0]['price'] = 1e-300
    prices[-1]['price'] = 1e300
    with pytest.raises(ValueError, match='derived_feature_invalid'):
        E.project(logical)


def test_root_features_require_actual_prefix_coverage_not_rolling_window():
    logical, _ = source()
    common = logical['common_context']
    common.update(epoch=100., confirmation_price=101.)
    signal = logical['signals'][0]
    signal['observed_signal'].update(epoch=98., price=100.)
    # The original 3-row prefix contains the root once and reaches confirmation.
    # Unknown side prevents a fabricated complete root-flow assessment.
    row = E.project(logical)['causal_prefix_evidence']['per_signal'][0]
    assert row['coverage']['root_age_sec'] == 2
    assert row['coverage']['root_interval_covered'] is True
    assert row['coverage']['root_clock_boundary_unambiguous'] is True
    assert row['values']['root_to_confirmation_return_pct'] == pytest.approx(1)
    assert row['values']['root_interval_min_change_pct'] == 0
    assert row['values']['root_interval_buy_qty_share_pct'] is None
    signal['recent_observed_prices'][-1]['side'] = 'BUY'
    row = E.project(logical)['causal_prefix_evidence']['per_signal'][0]
    assert row['values']['root_interval_buy_qty_share_pct'] == 75
    # A long root interval is not reconstructed from the last few prices.
    signal['observed_signal']['epoch'] = 90.
    row = E.project(logical)['causal_prefix_evidence']['per_signal'][0]
    assert row['coverage']['root_interval_covered'] is False
    assert row['values']['root_interval_min_change_pct'] is None
    assert row['values']['root_interval_buy_qty_share_pct'] is None


def test_same_clock_root_ambiguity_never_invents_root_interval_minimum_or_flow():
    logical, _ = source()
    logical['common_context'].update(epoch=100., confirmation_price=101.)
    signal = logical['signals'][0]
    signal['observed_signal'].update(epoch=98., price=100.)
    signal['recent_observed_prices'].insert(0, dict(age_sec=2., price=99., qty=100., side='SELL'))
    row = E.project(logical)['causal_prefix_evidence']['per_signal'][0]
    assert row['coverage']['root_interval_covered'] is True
    assert row['coverage']['root_clock_boundary_unambiguous'] is False
    assert row['values']['root_interval_min_change_pct'] is None
    assert row['values']['root_interval_buy_qty_share_pct'] is None


def test_future_root_clock_rejected_even_when_prefix_itself_is_past():
    logical, _ = source()
    logical['common_context'].update(epoch=100., confirmation_price=101.)
    logical['signals'][0]['observed_signal'].update(epoch=101., price=100.)
    with pytest.raises(ValueError, match='root_clock_invalid'):
        E.project(logical)


@pytest.mark.parametrize('candidate_only', [True, False])
def test_role_scoped_input_ablation_preserves_current_exact_request_and_decode(candidate_only):
    """Final holdout can compare unchanged CURRENT with enriched CANDIDATE.

    The default factorial intervention continues to enrich both roles. No
    original capture, registry, prompt or model is repaired or overwritten.
    """
    from src.engine.scalping import reversal_auxiliary_tuning as T
    fixture = next(iter(FIXTURES.values()))
    snapshot = [fixture['event'], fixture['source']]
    original = G.definition(U.V1.ARMS[1], input_version=U.VERSION)
    selected = G.definition(U.V1.ARMS[1], input_version=U.VERSION,
        prompt=original['prompt']+'\nInterpret only supplied facts.\n')
    registries = {role:G.compact_definition(value, research_wire_contract=OLD_W.contract())
        for role,value in [('current',original),('candidate',selected)]}
    before = copy.deepcopy((snapshot, registries))
    cfg = dict(causal_prefix_contract=E.contract())
    if candidate_only:
        cfg['causal_prefix_roles'] = ['candidate']
    requests = {}
    for role, registry in registries.items():
        plain = G.request(snapshot, registry)
        plain_logical = G.production_request(snapshot, registry)[0]
        actual = T.research_request(snapshot, registry, cfg, role)
        logical = T.research_logical_input(snapshot, registry, cfg, role)
        transformed = not candidate_only or role == 'candidate'
        if transformed:
            assert actual == E.transform_request(plain, plain_logical, contract=E.contract())
            assert logical == E.project(plain_logical)
            assert actual['paired_replay_id'] != plain['paired_replay_id']
            assert 'causal_prefix_evidence' in logical
        else:
            assert actual == plain
            assert P.digest(actual) == P.digest(plain)
            assert logical == plain_logical
            assert 'causal_prefix_evidence' not in logical
            assert 'offline_causal_prefix_contract' not in actual['candidate']
        assert actual['candidate']['system_prompt'] == plain['candidate']['system_prompt']
        assert actual['control'] == plain['control']
        for field in ('model','max_output_tokens','reasoning_effort'):
            assert actual['candidate'][field] == plain['candidate'][field]
        aliases = W.encode(logical)[2]
        if transformed:
            fid = next(f['id'] for f in logical['entry_setup_evidence_v1']['context_facts']
                       if f['id'].endswith('/observed_prefix_return_pct'))
            screen = dict(verdict='CAUTION',risk='PREFIX_PATH_CONCERN',fact=aliases[fid])
        else:
            screen = dict(verdict='PASS',risk='NO_BLOCKING_RISK',fact=aliases['observed_machine_signal'])
        raw = dict(assessed={aliases[s['ref']]:True for s in logical['signals']},screen=screen,confidence=51)
        raw_before = copy.deepcopy(raw)
        decoded, errors = T.response_projection(dict(candidate_response=raw),actual,logical,registry)
        assert errors == [] and decoded['risk_verdict'] == screen['verdict']
        assert raw == raw_before
        if transformed:
            # An enriched raw response cannot be decoded against the old input
            # by silently accepting a shifted short citation alias.
            _, old_errors = T.response_projection(dict(candidate_response=raw),actual,plain_logical,registry)
            assert old_errors
        requests[role] = actual
    assert requests['current']['control'] == requests['candidate']['control']
    assert (snapshot, registries) == before


def received_prefix(logical):
    common = logical['common_context']
    t, price = common['epoch'], common['confirmation_price']
    middle = price/1.002
    boundary = middle/.999
    def window(start, end, first_price, last_price, buy, sell):
        return dict(start_epoch=start, end_epoch=end, observation_count=4,
            positive_qty_observation_count=4, first_observed_epoch=start+1,
            last_observed_epoch=end, boundary_trade_epoch=start,
            boundary_trade_price=first_price, last_trade_price=last_price,
            return_pct=100*(last_price/first_price-1), buy_qty=buy, sell_qty=sell,
            unknown_qty=0., total_positive_qty=buy+sell,
            known_side_buy_qty_pct=100*buy/(buy+sell), known_side_qty_coverage_pct=100.)
    previous = window(t-30,t-10,boundary,middle,20.,80.)
    last = window(t-10,t,middle,price,80.,20.)
    return P.seal(dict(schema=E.SOURCE_PREFIX_SCHEMA,
        **{k:common[k] for k in ('opportunity_key','symbol','market','venue','source_item',
                                'native_epoch','native_sequence')},
        day=common['as_of'][:10], confirmation_epoch=t,
        source_receipt=dict(path='/frozen/normalized.json.gz',sha256='a'*64),
        prefix_sha256='b'*64, observed_prefix_start_epoch=t-40,
        observed_prefix_end_epoch=t, coverage_seconds=30., window_complete=True,
        windows=dict(previous20s=previous,last10s=last),
        price30s=dict(boundary_trade_price=boundary,boundary_trade_epoch=t-30,
            min_trade_price=middle,max_trade_price=price,last_trade_price=price,
            current_from_min_pct=100*(price/middle-1),return_pct=100*(price/boundary-1)), **P.AUTH))


def test_received_prefix_new_information_is_causal_bound_and_immutable():
    original, registry = source()
    evidence = received_prefix(original)
    before = copy.deepcopy((original,evidence,registry))
    enriched = E.project(original, source_prefix=evidence)
    leaf = enriched['causal_prefix_evidence']['received_prefix']
    assert leaf['values']['last10s_last_observed_boundary_return_pct'] == pytest.approx(.2)
    assert leaf['values']['previous20s_last_observed_boundary_return_pct'] == pytest.approx(-.1)
    assert leaf['values']['observed_boundary_return_rate_change_pct_points_per_sec'] == pytest.approx(.025)
    assert leaf['values']['known_side_buy_qty_change_pct_points'] == 60
    assert leaf['source_evidence_sha256'] == evidence['artifact_content_sha256']
    assert '/frozen/' not in str(leaf)
    req = W.request(request(original), original, W.contract())
    transformed = E.transform_request(req, original, contract=E.contract(), source_prefix=evidence)
    assert transformed['candidate_input'] == W.encode(enriched)[0]
    aliases = W.encode(enriched)[2]
    fid = E.SOURCE_PREFIX_SCHEMA+'/known_side_buy_qty_change_pct_points'
    raw = dict(assessed={aliases[s['ref']]:True for s in enriched['signals']},
        screen=dict(verdict='CAUTION',risk='RECEIVED_PREFIX_FLOW_CONCERN',fact=aliases[fid]),confidence=51)
    assert W.decode(raw,enriched,registry['base_arm'])['contradicting_fact_ids'] == [fid]
    assert E.validate_projected(original,enriched,source_prefix=evidence) == enriched
    assert (original,evidence,registry) == before


@pytest.mark.parametrize('defect', ['seal','opportunity','item','sequence','authority','future_prefix',
    'future_window','return','flow','quantity','extra_label','anchor_after_boundary'])
def test_received_prefix_tamper_future_leak_and_unbound_identity_are_rejected(defect):
    logical, _ = source()
    evidence = received_prefix(logical)
    if defect=='seal': evidence['prefix_sha256']='c'*64
    elif defect=='opportunity': evidence['opportunity_key']='d'*64
    elif defect=='item': evidence['source_item']='other_item'
    elif defect=='sequence': evidence['native_sequence']+=1
    elif defect=='authority': evidence['runtime_effect']=True
    elif defect=='future_prefix': evidence['observed_prefix_end_epoch']+=1
    elif defect=='future_window': evidence['windows']['last10s']['end_epoch']+=1
    elif defect=='return': evidence['windows']['last10s']['return_pct']=9.
    elif defect=='flow': evidence['windows']['last10s']['known_side_buy_qty_pct']=101.
    elif defect=='quantity': evidence['windows']['last10s']['sell_qty']=-1.
    elif defect=='extra_label': evidence['future_outcome']='WIN'
    elif defect=='anchor_after_boundary': evidence['windows']['last10s']['boundary_trade_epoch']+=1
    if defect!='seal': evidence=P.seal(evidence)
    with pytest.raises(ValueError,match='causal_received_prefix'):
        E.project(logical,source_prefix=evidence)


def test_received_prefix_incomplete_windows_stay_unknown_and_anchor_age_is_explicit():
    logical, _ = source()
    evidence = received_prefix(logical)
    evidence['windows']['previous20s']['boundary_trade_epoch']-=5
    evidence['price30s']['boundary_trade_epoch']-=5
    evidence=P.seal(evidence)
    leaf=E.project(logical,source_prefix=evidence)['causal_prefix_evidence']['received_prefix']
    assert leaf['windows']['previous20s']['boundary_observation_age_sec']==5
    assert leaf['price30s_boundary_observation_age_sec']==5
    assert leaf['values']['observed_boundary_return_rate_change_pct_points_per_sec']==pytest.approx(.024)
    evidence['observed_prefix_start_epoch']=evidence['confirmation_epoch']-12
    evidence['coverage_seconds']=12.
    evidence['window_complete']=False
    for win in evidence['windows'].values():
        for key in list(win):
            if key not in {'start_epoch','end_epoch','first_observed_epoch','last_observed_epoch',
                            'observation_count','positive_qty_observation_count'}:
                win[key]=None
    evidence['price30s']={k:None for k in evidence['price30s']}
    evidence=P.seal(evidence)
    enriched=E.project(logical,source_prefix=evidence)
    leaf=enriched['causal_prefix_evidence']['received_prefix']
    assert all(value is None for value in leaf['values'].values())
    assert not any(f['id'].startswith(E.SOURCE_PREFIX_SCHEMA+'/')
        for f in enriched['entry_setup_evidence_v1']['context_facts'])


def test_exact_received_prefix_in_study_snapshot_only_changes_candidate_input():
    from src.engine.scalping import reversal_auxiliary_tuning as T
    fixture = next(iter(FIXTURES.values()))
    original_snapshot = copy.deepcopy([fixture['event'],fixture['source']])
    definition = G.definition(U.V1.ARMS[1],input_version=U.VERSION)
    current = G.compact_definition(definition,research_wire_contract=OLD_W.contract())
    original_request = G.request(original_snapshot,current)
    original_logical = G.production_request(original_snapshot,current)[0]
    study_snapshot = copy.deepcopy(original_snapshot)
    evidence = received_prefix(original_logical)
    study_snapshot[1]['research_prefix_evidence'] = evidence
    before = copy.deepcopy(study_snapshot)
    assert G.request(study_snapshot,current) == original_request
    cfg = dict(causal_prefix_contract=E.contract(),causal_prefix_roles=['candidate'])
    assert T.research_request(study_snapshot,current,cfg,'current') == original_request
    assert T.research_logical_input(study_snapshot,current,cfg,'current') == original_logical
    request = T.research_request(study_snapshot,current,cfg,'candidate')
    logical = T.research_logical_input(study_snapshot,current,cfg,'candidate')
    assert request == E.transform_request(original_request,original_logical,
        contract=E.contract(),source_prefix=evidence)
    assert logical == E.project(original_logical,source_prefix=evidence)
    leaf = logical['causal_prefix_evidence']['received_prefix']
    assert leaf['source_evidence_sha256'] == evidence['artifact_content_sha256']
    aliases = W.encode(logical)[2]
    fid = E.SOURCE_PREFIX_SCHEMA+'/known_side_buy_qty_change_pct_points'
    raw = dict(assessed={aliases[s['ref']]:True for s in logical['signals']},
        screen=dict(verdict='CAUTION',risk='RECEIVED_PREFIX_FLOW_CONCERN',fact=aliases[fid]),confidence=51)
    decoded,errors = T.response_projection(dict(candidate_response=raw),request,logical,current)
    assert not errors and decoded['contradicting_fact_ids'] == [fid]
    assert study_snapshot == before and 'research_prefix_evidence' not in original_snapshot[1]
