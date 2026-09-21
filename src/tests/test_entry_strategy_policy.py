"""Raw policy replay, joint search and durable current-generation contracts."""
from copy import deepcopy
from datetime import datetime
import json

import pytest

from src.engine.scalping import entry_strategy_policy as strategy
from src.engine.scalping import entry_setup_evidence as evidence
from src.engine.scalping import ai_decision_quality as quality
from src.engine.scalping import mechanistic_entry_runtime_policy as runtime


def raw():
    return dict(effective_venue='KRX', session_bucket='KRX_REGULAR',
        current=dict(price=10000, fluctuation_pct=16),
        features=dict(curr_vs_micro_vwap_bp=90, curr_vs_ma5_bp=90,
            entry_order_flow_status='neutral', order_flow_pressure_score=64, order_flow_pressure_source='trusted_aggressor',
            entry_momentum_status='accelerating', tick_acceleration_ratio=2,
            buy_pressure_10t=65, net_aggressive_delta_10t=100,
            tick_aggressor_trusted_count=20, tick_aggressor_pressure_usable=True,
            quote_fresh_for_entry=True, quote_stale=False, quote_age_ms=100,
            tick_context_stale=False, tick_latest_age_ms=100,
            large_sell_print_detected=False, tick_context_quality='fresh_computed',
            tick_accel_source='same_second_burst_10ticks', spread_bp=20,
            top1_bid_notional=100000, top1_ask_notional=100000,
            top3_bid_notional=300000, top3_ask_notional=200000,
            fillability_score=70, would_fill_now=True, quote_depth_present=True,
            price_change_10t_pct=.1),
        entry_candle_context=dict(completed_bar_count=30,
            source_quality=dict(status='fresh_consistent',
                decision_window=dict(status='fresh_consistent', completed_bar_count=21)),
            structure=dict(returns_pct={str(n): .5 for n in (1,3,5,10,20,60)},
                slopes_pct_per_bar={str(n): .1 for n in (1,3,5,10,20,60)},
                peak_drawdown_pct=-.1, high_direction='up_or_flat', low_direction='up_or_flat',
                volume_ratio=1.3, volume_direction_alignment='bullish_confirmed',
                regime='breakout', alignment='positive')))


def setup(payload=None):
    payload = payload or raw()
    return evidence.build_entry_setup_evidence(exact_payload=payload,
        exact_analysis=quality.build_exact_payload_analysis_v1(payload, stage='entry', live_entry=True),
        recovery_analysis=quality.build_v2_13_recovery_confirmation_analysis_v1(payload, stage='entry'),
        balanced_policy=True)


def policy():
    return strategy.seed(evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1, ('KRX', 'KRX_REGULAR'))


def test_raw_strategic_block_recomputed_and_context_does_not_leak():
    original = setup()
    baseline = evidence.mechanistic_entry_policy_decision(original)
    candidate = policy()
    candidate['strategy']['nodes']['root']['profile'].update(
        overextension_runup_pct=20, overextension_vwap_bp=120, overextension_ma5_bp=120, tape_supportive_score=60)
    decision = evidence.mechanistic_entry_policy_decision(original, policy=candidate)
    assert baseline['action'] == 'BLOCK'
    assert decision['action'] == 'ENTER_NOW', decision
    assert decision['strategy_selection']['effective_thresholds']['overextension_runup_pct'] == 20
    assert evidence.mechanistic_entry_policy_decision(original) == baseline
    assert strategy.knob('overextension_runup_pct', 15) == 15
    assert not evidence.validate_entry_setup_evidence(decision['effective_setup_evidence'])


def test_missing_and_corrupt_raw_cannot_use_saved_labels():
    original = setup()
    original.pop('strategy_raw_input')
    with pytest.raises(ValueError, match='raw_input_missing'):
        evidence.mechanistic_entry_policy_decision(original, policy=policy())
    original = setup()
    original['strategy_raw_input']['current']['price'] += 1
    with pytest.raises(ValueError, match='raw_input_hash_invalid'):
        evidence.mechanistic_entry_policy_decision(original, policy=policy())


@pytest.mark.parametrize('field,value', [('quote_fresh_for_entry', False), ('tick_context_stale', True)])
def test_source_guards_survive_strategy_relaxation(field, value):
    payload = raw()
    payload['features'][field] = value
    candidate = policy()
    candidate['strategy']['nodes']['root']['profile'].update(overextension_runup_pct=20,
        overextension_vwap_bp=120, overextension_ma5_bp=120)
    decision = evidence.mechanistic_entry_policy_decision(setup(payload), policy=candidate)
    assert decision['action'] != 'ENTER_NOW'


def test_joint_cartesian_search_finds_three_coordinate_interaction_and_resumes():
    parent = evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1
    domains = {key: [strategy.REGISTRY[key][0], max(strategy.REGISTRY[key][1])]
        for key in ('trigger_buy_pressure', 'overextension_ma5_bp', 'ask_wall_ratio')}
    rows = list(strategy.joint_candidates(parent, ('KRX','KRX_REGULAR'), domains=domains, limit=8))
    assert len({strategy.digest(p) for p, _ in rows}) == 8
    assert rows[-1][1]['search_complete']
    assert list(strategy.joint_candidates(parent, ('KRX','KRX_REGULAR'), domains=domains, start=3, limit=5)) == rows[3:]
    # Nonmonotone oracle: only the triple joint change has positive value.
    def score(item):
        profile = item[0]['strategy']['nodes']['root']['profile']
        return 7 if all(profile[k] == max(v) for k,v in domains.items()) else -1
    assert max(map(score, rows)) == 7


def test_type_selection_boundary_unknown_parent_and_strict_graph():
    candidate = policy()
    parent = candidate['strategy']['nodes']['root']['profile']
    child = {**parent, 'trigger_buy_pressure': 65}
    candidate['strategy']['nodes'] = dict(root=dict(profile=parent,
        split=dict(feature='price', boundary=10000, lt='small', ge='large')),
        small=dict(profile=parent), large=dict(profile=child))
    assert not strategy.validate(candidate['strategy'])
    values, receipt = strategy.select(candidate, raw(), setup())
    assert receipt['leaf'] == 'large' and values['trigger_buy_pressure'] == 65
    missing = raw(); missing['current'].pop('price')
    assert strategy.select(candidate, missing, setup())[1]['fallback_reason'] == 'unknown_parent'
    candidate['strategy']['nodes']['root']['split']['ge'] = 'root'
    assert strategy.validate(candidate['strategy'])


def test_future_optional_metadata_is_unknown_but_unit_conflict_is_error():
    payload = raw()
    payload['strategy_metadata'] = dict(observed_at='2026-09-21T10:00:00+09:00', market_cap=dict(
        known_at='2026-09-21T11:00:00+09:00', effective_at='2026-09-21T09:00:00+09:00',
        unit='KRW', source_sha256='a'*64, corporate_action_consistent=True, value=1e12))
    assert strategy.features(payload, setup())['market_cap_krw'] is None
    payload['strategy_metadata']['market_cap']['unit'] = 'million_KRW'
    with pytest.raises(ValueError):
        strategy.features(payload, setup())


def candidate(parent=None):
    parent = parent or evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1
    machine = strategy.seed(parent, ('KRX', 'KRX_REGULAR'))
    machine['strategy']['nodes']['root']['profile']['trigger_buy_pressure'] = 55
    def arm(day, n):
        return dict(source_dates=[day], opportunity_ids=[day + ':' + str(i) for i in range(n)],
            changed_opportunity_ids=[day + ':' + str(i) for i in range(n)],
            source_complete=True, downstream_context_bound=True,
            economics=dict(status='supported_operating_comparison', incumbent=dict(net_pnl_krw=0),
                candidate=dict(net_pnl_krw=1, ev_pct=.001, worst=.001), daily_net_profit_delta_krw=1,
                robust_paired_delta_ev_lower_bound_pct=.0001))
    proof = dict(train=arm('2026-09-10', 10), holdout=arm('2026-09-11', 3))
    return dict(schema='main_entry_strategy_candidate_v2', scope=['KRX', 'KRX_REGULAR'],
        parent_policy=deepcopy(parent), parent_sha256=strategy.digest(parent), policy=machine, policy_sha256=strategy.digest(machine),
        evidence=proof, evidence_sha256=strategy.digest(proof), selected_without_holdout=True)


def test_small_positive_net_can_qualify_without_five_days_or_ten_basis_points():
    item = candidate()
    assert strategy.promotion_errors(item, evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1, ('KRX','KRX_REGULAR')) == []
    item['evidence']['holdout']['economics']['candidate']['net_pnl_krw'] = -1
    item['evidence_sha256'] = strategy.digest(item['evidence'])
    assert strategy.promotion_errors(item, evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1, ('KRX','KRX_REGULAR'))


def activation_source(tmp_path, item):
    from src.engine.scalping import ai_action_outcome_calibration as calibration
    report = calibration._with_artifact_content_sha256(dict(schema=calibration.SCHEMA,
        target_date='2026-09-11', clean_tuning_baseline_date='2026-06-05',
        report_scope='main_mechanistic_entry', noncompact_sections_refreshed=True,
        strategy_refinements_by_scope={'KRX|KRX_REGULAR': dict(promotion_pass=True, candidate=item)}))
    path = tmp_path / 'strategy_source.json'
    path.write_text(json.dumps(report))
    return path


def test_immediate_generation_persists_over_dates_and_invalid_successor(tmp_path):
    from src.tests.test_mechanistic_entry_runtime_policy import initial
    previous = initial(tmp_path)
    item = candidate(previous['machine_policy'])
    source = activation_source(tmp_path, item)
    receipt = runtime.activate_strategy_report(source, data_root=tmp_path,
        now=datetime(2026,9,14,12,tzinfo=runtime.KST))
    assert receipt['status'] == 'activated'
    active = runtime.load_effective(data_root=tmp_path, target_date='2026-09-14')
    assert active['machine_policy'] == item['policy']
    assert runtime.load_effective(data_root=tmp_path, target_date='2026-09-21') == active
    assert runtime.load(data_root=tmp_path, target_date='2026-09-14') == previous
    assert runtime.activate_strategy_report(source, data_root=tmp_path,
        now=datetime(2026,9,14,13,tzinfo=runtime.KST))['status'] == 'already_active'
    assert runtime.load_effective(data_root=tmp_path, target_date='2026-09-15') == active
    path = runtime.root(tmp_path) / 'current.json'
    path.write_text('{}')
    with pytest.raises(ValueError, match='current_receipt'):
        runtime.load_effective(data_root=tmp_path, target_date='2026-09-15')


def test_strategy_metadata_and_profile_mutations_invalidate_bundle(tmp_path):
    from src.tests.test_mechanistic_entry_runtime_policy import initial
    previous = initial(tmp_path)
    receipt = runtime.activate_strategy_report(activation_source(tmp_path, candidate(previous['machine_policy'])),
        data_root=tmp_path, now=datetime(2026,9,14,12,tzinfo=runtime.KST))
    path = runtime.root(tmp_path) / 'generations' / (receipt['bundle_sha256'] + '.json')
    data = json.loads(path.read_text())
    data['machine_policy']['strategy']['nodes']['root']['profile']['trigger_buy_pressure'] = 60
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='bundle_contract'):
        runtime.load_effective(data_root=tmp_path, target_date='2026-09-15')


def test_identifiable_missing_raw_row_is_isolated_without_dropping_denominator():
    from src.engine.scalping.ai_action_outcome_calibration import build_main_strategy_refinement
    rows = [dict(decision_trace_id='missing', source_date='2026-09-11', setup_evidence={}),
            dict(decision_trace_id='supported', source_date='2026-09-11', setup_evidence=setup())]
    result = build_main_strategy_refinement(rows,
        parent=evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1,
        scope=('KRX','KRX_REGULAR'), source_contract={})
    assert result['population_count'] == 2
    assert result['supported_population_count'] == 1
    assert result['source_exclusions'] == [dict(decision_trace_id='missing', reason='strategy_predecision_primitives_missing')]
    assert result['status'] == 'hold_sample'


def test_real_kernel_requires_joint_wall_trigger_and_execution_threshold_change():
    payload = raw()
    payload['features'].update(entry_order_flow_status='supportive', order_flow_pressure_score=70,
        buy_pressure_10t=58, spread_bp=60, top1_ask_notional=600000,
        top3_bid_notional=1000000, top3_ask_notional=600000)
    source = setup(payload)
    parent = deepcopy(evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1)
    parent['thresholds']['maximum_spread_bp'] = 50.
    domains = dict(ask_wall_ratio=[5.,7.], trigger_buy_pressure=[60.,55.], maximum_spread_bp=[50.,80.])
    decisions = [(item, evidence.mechanistic_entry_policy_decision(source, policy=item))
        for item, _ in strategy.joint_candidates(parent, ('KRX','KRX_REGULAR'), domains=domains, limit=8)]
    entering = [(item, decision) for item, decision in decisions if decision['action'] == 'ENTER_NOW']
    assert len(entering) == 1
    profile = entering[0][0]['strategy']['nodes']['root']['profile']
    assert all(profile[k] == v[1] for k,v in domains.items())
    assert {d['action'] for _,d in decisions} == {'BLOCK','RECHECK','ENTER_NOW'}


def test_provider_ledger_excludes_raw_replay_without_mutating_custody():
    from src.engine.ai_engine_openai import _entry_provider_ledger
    original = setup()
    before = deepcopy(original)
    sent = _entry_provider_ledger(original)
    assert 'strategy_raw_input' not in sent
    assert 'strategy_raw_sha256' not in sent
    assert sent['positive_facts'] == original['positive_facts']
    assert sent['evidence_sha256'] == strategy.digest({k:v for k,v in sent.items() if k != 'evidence_sha256'})
    assert original == before
    assert not evidence.validate_entry_setup_evidence(sent)


def historical_payload():
    payload = raw()
    payload['strategy_observed_at'] = '2026-09-17T09:30:05+09:00'
    payload['entry_candle_context']['bars'] = [dict(t=f'09:{i:02d}', o=10000+i,
        h=10002+i, l=9999+i, c=10001+i, v=100, forming=False) for i in range(10,30)]
    return payload


def test_legacy_local_structure_is_rebuilt_from_captured_tail_without_future_lookup():
    payload = historical_payload()
    payload['entry_candle_context']['structure']['regime'] = 'failed_breakout'
    original = setup(payload)
    decision = evidence.mechanistic_entry_policy_decision(original, policy=policy())
    rebuilt = decision['effective_setup_evidence']
    assert rebuilt['structure_contract_version'] == 'entry_local_breakout_completed_v1'
    assert rebuilt['local_breakout']['recheck_required'] is True
    assert decision['action'] != 'ENTER_NOW'
    assert original['strategy_raw_input'] == payload
    future = deepcopy(original)
    future['strategy_raw_input']['entry_candle_context']['bars'][-1]['t'] = '09:31'
    future['strategy_raw_sha256'] = strategy.digest(future['strategy_raw_input'])
    with pytest.raises(ValueError, match='future'):
        evidence.mechanistic_entry_policy_decision(future, policy=policy())


def test_truncated_historical_tail_does_not_support_longer_lookback():
    candidate_policy = policy()
    candidate_policy['strategy']['nodes']['root']['profile']['breakout_lookback'] = 20
    with pytest.raises(ValueError, match='tail_truncated'):
        evidence.mechanistic_entry_policy_decision(setup(historical_payload()), policy=candidate_policy)
