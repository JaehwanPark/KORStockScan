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


def research_row(payload=None):
    return dict(decision_trace_id='attempt-1', source_date='2026-09-10',
        stock_code='005930', scanner_promotion_id='promotion-1',
        setup_evidence=setup(payload), comparison={})


def research_policy():
    value = policy()
    value['strategy']['nodes']['root']['profile'].update(
        overextension_runup_pct=20, overextension_vwap_bp=120,
        overextension_ma5_bp=120, tape_supportive_score=60)
    return value


def one_research_candidate(monkeypatch):
    monkeypatch.setattr(strategy, 'joint_candidates', lambda *a, **kw: iter([
        (research_policy(), dict(cursor=1, domain_size=1, domain_sha256='a'*64, search_complete=True))]))


def test_one_raw_opportunity_can_generate_research_without_cost_or_holdout(monkeypatch):
    from src.engine.scalping import ai_action_outcome_calibration as calibration
    one_research_candidate(monkeypatch)
    result = calibration.build_main_strategy_refinement([research_row()],
        parent=evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1,
        scope=('KRX', 'KRX_REGULAR'), source_contract={})
    assert result['evaluated_candidate_count'] == 1
    assert result['status'] == 'hold_sample' and result['promotion_pass'] is False
    assert result['candidate'] is None and result['research_only'] is True
    item = result['research_candidates'][0]
    assert item['action_transition_counts'] == {'BLOCK->ENTER_NOW': 1}
    assert item['allowed_runtime_apply'] is False
    assert item['downstream_context_bound'] is False
    assert item['changed_attempts'][0]['raw_sha256'] == research_row()['setup_evidence']['strategy_raw_sha256']


def test_research_cache_changes_with_raw_even_when_trace_ids_unchanged(monkeypatch):
    from src.engine.scalping import ai_action_outcome_calibration as calibration
    one_research_candidate(monkeypatch)
    kwargs = dict(parent=evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1,
        scope=('KRX', 'KRX_REGULAR'), source_contract={})
    first = calibration.build_main_strategy_refinement([research_row()], **kwargs)
    previous = {**first, 'candidate': {'parent_sha256': 'different'}, 'cache_marker': True}
    changed = raw(); changed['current']['price'] += 10
    second = calibration.build_main_strategy_refinement([research_row(changed)], previous=previous, **kwargs)
    assert second['input_sha256'] != first['input_sha256']
    assert 'cache_marker' not in second


def test_incumbent_hierarchy_is_not_replaced_by_strategy_seed(monkeypatch):
    from src.engine.scalping import ai_action_outcome_calibration as calibration
    one_research_candidate(monkeypatch)
    parent = deepcopy(evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1)
    parent['hierarchy'] = {'test_marker': 'must_reach_actual_parent'}
    actual = calibration.mechanistic_entry_policy_decision
    observed = []
    def decision(value, *, policy):
        if 'strategy' not in policy:
            observed.append(policy)
            return dict(action='RECHECK')
        return actual(value, policy=policy)
    monkeypatch.setattr(calibration, 'mechanistic_entry_policy_decision', decision)
    result = calibration.build_main_strategy_refinement([research_row()], parent=parent,
        scope=('KRX','KRX_REGULAR'), source_contract={})
    assert observed == [parent]
    assert result['research_candidates'][0]['action_transition_counts'] == {'RECHECK->ENTER_NOW': 1}


def test_equal_setup_does_not_reuse_a_different_auxiliary_machine_assessment(monkeypatch):
    from src.engine.scalping import ai_action_outcome_calibration as calibration
    one_research_candidate(monkeypatch)
    row = research_row()
    decision = evidence.mechanistic_entry_policy_decision(row['setup_evidence'], policy=research_policy())
    provider_assessment = {k:v for k,v in decision.items() if k not in {'strategy_selection','effective_setup_evidence'}}
    row['operating_comparison_input'] = {'input': {
        'entry_setup_evidence_v1': decision['effective_setup_evidence'],
        'mechanistic_entry_assessment': {**provider_assessment, 'action':'BLOCK'}}}
    kwargs = dict(parent=evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1,
        scope=('KRX','KRX_REGULAR'), source_contract={})
    result = calibration.build_main_strategy_refinement([row], **kwargs)
    assert result['research_candidates'][0]['downstream_context_bound'] is False
    row['operating_comparison_input']['input']['mechanistic_entry_assessment'] = provider_assessment
    result = calibration.build_main_strategy_refinement([row], **kwargs)
    assert result['research_candidates'][0]['downstream_context_bound'] is True
    assert result['promotion_pass'] is False  # AI parity alone is not owner economics.


@pytest.mark.parametrize('change', [dict(h=9998), dict(v=-1), dict(dt='2026-09-09T09:00:00+09:00')])
def test_full_completed_bar_replay_rejects_invalid_ohlcv_and_other_session(change):
    payload = raw()
    bar = dict(dt='2026-09-10T09:00:00+09:00', o=10000, h=10002, l=9999, c=10001,
        v=100, forming=False, partial_volume=False)
    body = dict(observed_at='2026-09-10T09:02:00+09:00', bars=[{**bar, **change}])
    payload['entry_candle_context'].update(completed_bar_count=1,
        strategy_completed_bars=dict(body=body, sha256=strategy.digest(body)))
    item = policy(); item['strategy']['nodes']['root']['profile']['structure_volume_confirm'] = 1.3
    with pytest.raises(ValueError, match='ohlcv_or_session_invalid'):
        strategy.rebuild(setup(payload), item)


def machine_cost_row(hit='target_first'):
    row = research_row()
    row.update(stock_code='005930', effective_venue='KRX', session_bucket='KRX_REGULAR')
    row['scanner_promotion_id'] = 'opportunity-1'
    row['comparison'] = dict(incumbent_machine_action='BLOCK',
        entry_path_first_hit=hit, entry_path_target_pct=.5, entry_path_adverse_pct=-.5,
        conservative_execution_cost_pct=.2,
        entry_cost_contract=dict(schema='entry_round_trip_cost_v1', source_date=row['source_date'],
            effective_venue='KRX', session_bucket='KRX_REGULAR', basis='source_bound_estimate',
            source_sha256='a'*64, components_pct=dict(buy_fee=.01, sell_fee=.01, sell_tax=.15, slippage=.03)))
    row['entry_quality_contract_valid'] = True
    row['entry_quality_path'] = dict(schema='entry_quality_path_v1', status='evaluable',
        first_hit={'target_first':'net_target_first', 'adverse_first':'exact_stop_first'}.get(hit, hit),
        gross_net_target_pct=.5, exact_stop_distance_pct=-.5, conservative_execution_cost_pct=.2)
    return row


def test_machine_policy_selection_needs_no_ai_or_operating_replay(monkeypatch):
    from src.engine.scalping import ai_action_outcome_calibration as c
    one_research_candidate(monkeypatch)
    monkeypatch.setattr(c, '_machine_sequence_operating_metrics', lambda *a, **kw: pytest.fail('downstream replay invoked'))
    result = c.build_main_strategy_refinement([machine_cost_row()],
        parent=evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1, scope=('KRX','KRX_REGULAR'),
        source_contract={}, machine_policy_only=True)
    assert result['status'] == 'selected_machine_policy'
    assert result['machine_policy'] == research_policy()
    assert result['auxiliary_ai_required'] is False
    assert result['machine_evidence']['train']['economics']['paired_admission_delta_pct'] == pytest.approx(.3)
    assert result['promotion_pass'] is True and result['allowed_runtime_apply'] is False
    assert strategy.promotion_errors(result, evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1,
        ('KRX','KRX_REGULAR')) == ['strategy_candidate_schema_invalid']


@pytest.mark.parametrize('hit', ['neither', 'same_bar_ambiguous', None])
def test_machine_admission_does_not_invent_terminal_outcomes(hit):
    from src.engine.scalping import ai_action_outcome_calibration as c
    value = c._machine_admission_metrics([machine_cost_row(hit)], ['ENTER_NOW'])
    assert value['paired_admission_delta_pct'] is None
    assert value['excluded_attempt_counts'] == {'terminal_path_censored': 1}


def test_machine_admission_cost_and_episode_weighting_ignore_ai():
    from src.engine.scalping import ai_action_outcome_calibration as c
    good = machine_cost_row()
    good['operating_comparison_input'] = dict(incumbent_verdict='VETO')
    bad = machine_cost_row('adverse_first'); bad['scanner_promotion_id'] = 'second'
    value = c._machine_admission_metrics([good, good, bad], ['ENTER_NOW']*3)
    assert value['paired_admission_delta_pct'] == pytest.approx(-.2)
    assert value['comparable_opportunity_count'] == 2
    good['comparison']['entry_cost_contract']['components_pct'].pop('sell_tax')
    assert c._machine_admission_metrics([good], ['ENTER_NOW'])['paired_admission_delta_pct'] is None


def test_machine_admission_uses_cost_bound_path_not_lower_legacy_target():
    from src.engine.scalping import ai_action_outcome_calibration as c
    row = machine_cost_row()
    row['comparison']['entry_path_target_pct'] = .1  # Below the recorded .2% cost.
    value = c._machine_admission_metrics([row], ['ENTER_NOW'])
    assert value['selected_path_ev_pct'] == pytest.approx(.3)
    row['entry_quality_path']['conservative_execution_cost_pct'] = .1
    assert c._machine_admission_metrics([row], ['ENTER_NOW'])['selected_path_ev_pct'] is None
    row.pop('entry_quality_path')
    assert c._machine_admission_metrics([row], ['ENTER_NOW'])['selected_path_ev_pct'] is None


def test_machine_policy_selects_best_available_even_when_losing(monkeypatch):
    from src.engine.scalping import ai_action_outcome_calibration as c
    one_research_candidate(monkeypatch)
    result = c.build_main_strategy_refinement([machine_cost_row('adverse_first')],
        parent=evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1, scope=('KRX','KRX_REGULAR'),
        source_contract={}, machine_policy_only=True)
    assert result['machine_policy'] == research_policy()
    assert result['promotion_pass'], result['promotion_errors']
    assert result['machine_evidence']['train']['economics']['selected_path_ev_pct'] == pytest.approx(-.7)
    losing = machine_cost_row('adverse_first')
    losing['entry_quality_path']['exact_stop_distance_pct'] = -6.
    result = c.build_main_strategy_refinement([losing],
        parent=evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1, scope=('KRX','KRX_REGULAR'),
        source_contract={}, machine_policy_only=True)
    assert result['promotion_pass'], result['promotion_errors']
    assert result['machine_evidence']['train']['economics']['worst_selected_path_pct'] == pytest.approx(-6.2)


def test_machine_policy_cli_does_not_invoke_full_loop(monkeypatch, tmp_path, capsys):
    from src.engine.scalping import ai_action_outcome_calibration as c
    monkeypatch.setattr(c, 'load_machine_observation_rows', lambda *a, **kw: ([], {}))
    monkeypatch.setattr(c, '_machine_ai_natural_source_receipt', lambda *a: {})
    monkeypatch.setattr(c, 'ensure_machine_economic_reference', lambda **kw: {'status': 'existing_verified_sources_preserved'})
    monkeypatch.setattr(c, 'build_main_mechanistic_report', lambda **kw: pytest.fail('full loop'))
    assert c.main(['--target-date','2026-09-17','--data-root',str(tmp_path),'--machine-policy-only','--write']) == 0
    path = tmp_path/'report/ai_decision_action_outcome_calibration/machine_policy_2026-09-17.json'
    result = json.loads(path.read_text())
    assert c._artifact_content_sha256_valid(result)
    assert result['policy_by_scope'] == {} and result['allowed_runtime_apply'] is False
    assert not (tmp_path/'runtime/mechanistic_entry_policy/current.json').exists()


def test_machine_policy_holdout_does_not_choose_train_winner(monkeypatch):
    from src.engine.scalping import ai_action_outcome_calibration as c
    one_research_candidate(monkeypatch)
    train = machine_cost_row(); holdout = machine_cost_row('adverse_first')
    holdout.update(source_date='2026-09-11', decision_trace_id='attempt-2')
    holdout['comparison']['entry_cost_contract']['source_date'] = '2026-09-11'
    result = c.build_main_strategy_refinement([train, holdout],
        parent=evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1, scope=('KRX','KRX_REGULAR'),
        source_contract={}, machine_policy_only=True)
    assert result['machine_policy'] == research_policy()
    assert result['machine_evidence']['holdout']['economics']['paired_admission_delta_pct'] == pytest.approx(-.7)
    assert result['promotion_pass'], result['promotion_errors']
    assert result['allowed_runtime_apply'] is False


def test_machine_selection_scores_nonentry_and_existing_entry_loss_avoidance():
    from src.engine.scalping import ai_action_outcome_calibration as c
    missed = machine_cost_row(); missed['comparison']['incumbent_machine_action'] = 'RECHECK'
    existing = machine_cost_row('adverse_first'); existing['comparison']['incumbent_machine_action'] = 'ENTER_NOW'
    result = c._machine_admission_metrics([missed, existing], ['ENTER_NOW', 'BLOCK'])
    assert result['paired_admission_delta_pct'] == pytest.approx(.5)
    assert result['comparable_opportunity_count'] == 1
    assert result['excluded_attempt_counts'] == {}
    assert result['transition_attempt_counts']['existing_failure_avoided'] == 1


@pytest.mark.parametrize('holdout_hit', [None, 'adverse_first'])
def test_machine_policy_activates_and_carries_without_auxiliary_result(monkeypatch, tmp_path, holdout_hit):
    from src.engine.scalping import ai_action_outcome_calibration as c
    from src.tests.test_mechanistic_entry_runtime_policy import initial
    previous = initial(tmp_path)
    one_research_candidate(monkeypatch)
    rows = [machine_cost_row()]
    if holdout_hit:
        row = machine_cost_row(holdout_hit)
        row.update(source_date='2026-09-11', decision_trace_id='held-attempt')
        row['comparison']['entry_cost_contract']['source_date'] = row['source_date']
        rows.append(row)
    result = c.build_main_strategy_refinement(rows,
        parent=previous['machine_policy'], scope=('KRX','KRX_REGULAR'), source_contract={}, machine_policy_only=True)
    assert result['promotion_pass'], result['promotion_errors']
    source = activation_source(tmp_path, result['candidate'])
    receipt = runtime.activate_strategy_report(source, data_root=tmp_path,
        now=datetime(2026,9,14,12,tzinfo=runtime.KST))
    assert receipt['status'] == 'activated'
    active = runtime.load_effective(data_root=tmp_path,target_date='2026-09-21')
    assert active['machine_policy'] == result['machine_policy']
    assert active['ai_policy'] == previous['ai_policy']
    assert active['hard_guards_unchanged'] is True
    assert runtime.activate_strategy_report(source, data_root=tmp_path,
        now=datetime(2026,9,14,13,tzinfo=runtime.KST))['status'] == 'already_active'


def test_local_priority_keeps_joint_frontier_and_resume():
    parent = evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1
    domains = {k:[strategy.REGISTRY[k][0],max(strategy.REGISTRY[k][1])] for k in
        ('trigger_buy_pressure','overextension_ma5_bp','ask_wall_ratio')}
    rows = list(strategy.joint_candidates(parent,('KRX','KRX_REGULAR'),domains=domains,local_first=True,limit=96))
    assert rows[-1][1]['search_complete'] and len(rows)==96
    assert rows[3:] == list(strategy.joint_candidates(parent,('KRX','KRX_REGULAR'),domains=domains,local_first=True,start=3,limit=96))
    assert len({strategy.digest(p) for p,_ in rows if p}) >= 4


def test_machine_scope_selection_prioritizes_win_rate_over_larger_profit():
    def choice(win, net):
        return dict(promotion_pass=True, candidate=dict(evaluation_basis='machine_nonentry_opportunity_v1',
            evidence=dict(train=dict(economics=dict(win_rate_pct=win, selected_path_ev_pct=net,
                paired_admission_delta_pct=net, selected_opportunity_count=20)))))
    source = dict(strategy_refinements_by_scope=dict(high_win=choice(90,.1), high_profit=choice(60,2.), loss=choice(95,-.1)))
    assert strategy.select_report_candidate(source)[0] == 'loss'
    source['strategy_refinements_by_scope'] = dict(loss=choice(60,-.1), worse_loss=choice(60,-.2))
    assert strategy.select_report_candidate(source)[0] == 'loss'


def test_machine_win_rate_counts_costs_and_does_not_inflate_rechecks():
    from src.engine.scalping import ai_action_outcome_calibration as c
    good = machine_cost_row(); bad = machine_cost_row('adverse_first')
    bad['scanner_promotion_id'] = 'second'
    result = c._machine_admission_metrics([good,good,bad],['ENTER_NOW']*3)
    assert result['win_rate_pct'] == 50
    assert result['selected_opportunity_count'] == 2
    good['entry_quality_path']['gross_net_target_pct'] = .1
    assert c._machine_admission_metrics([good],['ENTER_NOW'])['win_rate_pct'] == 0


def test_machine_break_even_policy_is_allowed(monkeypatch):
    from src.engine.scalping import ai_action_outcome_calibration as c
    one_research_candidate(monkeypatch)
    row = machine_cost_row(); row['entry_quality_path']['gross_net_target_pct'] = .2
    result = c.build_main_strategy_refinement([row],
        parent=evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1, scope=('KRX','KRX_REGULAR'), source_contract={}, machine_policy_only=True)
    assert result['machine_policy'] is not None
    assert result['promotion_pass'], result['promotion_errors']
    assert result['machine_evidence']['train']['economics']['selected_path_ev_pct'] == pytest.approx(0.)
    assert strategy.select_report_candidate({'strategy_refinements_by_scope':{'KRX|KRX_REGULAR':result}})[0] == 'KRX|KRX_REGULAR'


def test_nonentry_search_resumes_without_repeating_prior_candidates(monkeypatch):
    from src.engine.scalping import ai_action_outcome_calibration as c
    starts=[]
    def candidates(*args, **kw):
        starts.append(kw['start'])
        yield research_policy(), dict(cursor=kw['start']+1,domain_size=10,domain_sha256='a'*64,search_complete=False)
    monkeypatch.setattr(strategy,'joint_candidates',candidates)
    kwargs=dict(parent=evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1,scope=('KRX','KRX_REGULAR'),source_contract={},machine_policy_only=True)
    first=c.build_main_strategy_refinement([machine_cost_row('same_bar_ambiguous')],**kwargs)
    second=c.build_main_strategy_refinement([machine_cost_row('same_bar_ambiguous')],previous=first,**kwargs)
    assert starts==[0,1]
    assert second['evaluated_candidate_count']==1 and len(second['machine_candidate_scores'])==1
    assert second['train_checkpoint']['group_counts']['legacy']['deduplicated'] == 1
    changed=machine_cost_row('same_bar_ambiguous');changed['comparison']['entry_path_adverse_pct']=-.6
    third=c.build_main_strategy_refinement([changed],previous=second,**kwargs)
    assert starts[-1]==0 and third['evaluated_candidate_count']==1


def test_frozen_machine_policy_revalidates_without_researching_holdout(monkeypatch):
    from src.engine.scalping import ai_action_outcome_calibration as c
    one_research_candidate(monkeypatch)
    rows = [machine_cost_row(), machine_cost_row('adverse_first')]
    rows[1].update(source_date='2026-09-11', decision_trace_id='held-attempt')
    rows[1]['comparison']['entry_cost_contract']['source_date'] = rows[1]['source_date']
    kwargs = dict(parent=evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1,
        scope=('KRX','KRX_REGULAR'), source_contract={}, machine_policy_only=True)
    previous = c.build_main_strategy_refinement(rows, **kwargs)
    previous.update(input_sha256='old-objective-version', promotion_pass=False)
    monkeypatch.setattr(strategy, 'joint_candidates', lambda *a, **kw: pytest.fail('used holdout researched'))
    result = c.build_main_strategy_refinement(rows, previous=previous, **kwargs)
    assert result['promotion_pass'], result['promotion_errors']
    assert result['machine_policy'] == previous['machine_policy']
    assert result['machine_evidence']['holdout']['economics']['selected_path_ev_pct'] < 0
    assert result['selection_status'] == 'frozen_before_same_holdout_revision'


def test_full_registry_budget_reaches_joint_and_selector_groups():
    parent = evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1
    rows = list(strategy.joint_candidates(parent, ('KRX','KRX_REGULAR'),
        selectors=[None, ('price', 20000, 'lt'), ('spread_bp', 15, 'ge')], local_first=True))
    from collections import Counter
    assert len(strategy.registry_contract()) == 82
    assert Counter(p['allocated_group'] for _,p in rows) == strategy.SEARCH_BUDGET
    valid_groups = {p['group'] for c,p in rows if c}
    assert valid_groups == set(strategy.SEARCH_BUDGET)
    assert any(c and len(p['changed_coordinates']) == 3 for c,p in rows)
    assert any(c and len(c['strategy']['nodes']) > 1 for c,p in rows)
    covered = {n for c,p in rows if c for n in p['changed_coordinates']}
    assert covered == set(strategy.REGISTRY)
    assert rows[41:] == list(strategy.joint_candidates(parent, ('KRX','KRX_REGULAR'),
        selectors=[None, ('price', 20000, 'lt'), ('spread_bp', 15, 'ge')], local_first=True, start=41))
    assert rows[-1][1]['search_complete'] and not rows[-1][1]['cartesian_exhausted']


def test_missing_row_uses_parent_without_freezing_supported_row():
    parent = policy()
    child = strategy._mutate_tree(parent, {'tape_supportive_score': 60}, None)
    original = setup()
    raw = original['strategy_raw_input']
    selected, receipt = strategy.select(child, raw, original)
    assert selected['tape_supportive_score'] == 60
    raw = deepcopy(raw)
    raw['features'].pop('order_flow_pressure_score', None)
    selected, receipt = strategy.select(child, raw, original)
    assert selected == strategy.default_profile(parent)
    assert receipt['fallback_reason'] == 'source_missing_parent'
    assert receipt['unsupported_coordinates'] == ['tape_supportive_score']


def test_existing_tree_leaf_and_fallback_survive_mutation():
    parent = strategy._mutate_tree(policy(), {'trigger_buy_pressure': 55}, ('price', 20000, 'lt'))
    child = strategy._mutate_tree(parent, {'ask_wall_ratio': 7}, None)
    original = setup()
    chosen, receipt = strategy.select(child, original['strategy_raw_input'], original)
    assert chosen['trigger_buy_pressure'] == 55 and chosen['ask_wall_ratio'] == 7
    assert len(child['strategy']['nodes']) == 3
    split = strategy._mutate_tree(parent, {'ask_wall_ratio': 7}, ('spread_bp', 20, 'both'))
    assert len(split['strategy']['nodes']) == 10 and not strategy.validate(split['strategy'])
    assert strategy.select(split, original['strategy_raw_input'], original)[0]['trigger_buy_pressure'] == 55
    raw = deepcopy(original['strategy_raw_input']); raw['features'].pop('spread_bp', None)
    assert strategy.select(split, raw, original)[0] == strategy.select(parent, raw, original)[0]


def test_machine_train_best_is_resumed_before_holdout(monkeypatch):
    from src.engine.scalping import ai_action_outcome_calibration as c
    def candidates(*args, **kw):
        if kw['start'] == 0:
            yield research_policy(), dict(cursor=1, domain_size=2, search_complete=False)
        else:
            yield policy(), dict(cursor=2, domain_size=2, search_complete=True)
    monkeypatch.setattr(strategy, 'joint_candidates', candidates)
    kw = dict(parent=evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1, scope=('KRX','KRX_REGULAR'),
              source_contract={}, machine_policy_only=True)
    rows = [machine_cost_row(), machine_cost_row('adverse_first')]
    rows[1].update(source_date='2026-09-11', decision_trace_id='held-attempt')
    rows[1]['comparison']['entry_cost_contract']['source_date'] = '2026-09-11'
    first = c.build_main_strategy_refinement(rows, **kw)
    assert first['selection_state'] == 'searching_train' and first['candidate'] is None
    assert first['train_checkpoint']['best'] and 'holdout' not in first['train_checkpoint']['best_evidence']
    second = c.build_main_strategy_refinement(rows, previous=first, **kw)
    assert second['machine_policy'] == research_policy()
    assert second['selection_state'] == 'holdout_evaluated' and second['promotion_pass']


def test_opportunity_identity_missing_promotion_uses_attempt():
    from src.engine.scalping import ai_action_outcome_calibration as c
    left = machine_cost_row(); right = deepcopy(left)
    left.pop('scanner_promotion_id', None); right.pop('scanner_promotion_id', None)
    right['decision_trace_id'] = 'second-attempt'
    assert c._machine_opportunity_id(left) != c._machine_opportunity_id(right)
    assert c._machine_admission_metrics([left,right], ['ENTER_NOW']*2)['selected_opportunity_count'] == 2


def test_invalid_high_score_scope_cannot_prevent_qualified_scope_activation(tmp_path):
    from src.tests.test_mechanistic_entry_runtime_policy import initial
    from src.engine.scalping import ai_action_outcome_calibration as c
    previous = initial(tmp_path)
    source_path = activation_source(tmp_path, candidate(previous['machine_policy']))
    source = json.loads(source_path.read_text())
    source['strategy_refinements_by_scope']['NXT|NXT_REGULAR'] = dict(promotion_pass=False,
        candidate=dict(evaluation_basis='machine_nonentry_opportunity_v1',
                       evidence=dict(train=dict(economics=dict(win_rate_pct=100, selected_path_ev_pct=10.)))))
    source_path.write_text(json.dumps(c._with_artifact_content_sha256(source)))
    applied = runtime.activate_strategy_report(source_path, data_root=tmp_path,
        now=datetime(2026,9,14,12,tzinfo=runtime.KST))
    assert applied['scopes'] == ['KRX|KRX_REGULAR']
    assert 'NXT|NXT_REGULAR' in applied['dispositions']
    assert runtime.validate_attempt_generation(previous['bundle_sha256'], data_root=tmp_path,
        now=datetime(2026,9,14,12,tzinfo=runtime.KST))['reason'] == 'policy_generation_changed'
    assert runtime.validate_attempt_generation(applied['bundle_sha256'], data_root=tmp_path,
        now=datetime(2026,9,14,12,tzinfo=runtime.KST))['allowed']


def test_canonical_market_cap_snapshot_uses_official_unit_without_legacy_rewrite(monkeypatch):
    from src.utils import kiwoom_utils as k
    monkeypatch.setattr(k, 'fetch_kiwoom_api_continuous', lambda *a, **kw: [dict(mac='2500', stk_nm='sample')])
    result = k.get_basic_info_ka10001('not-a-live-token', '123456')
    assert result['Marcap'] == 2500
    metadata = result['StrategyMetadata']
    assert metadata['market_cap']['value'] == 250_000_000_000
    assert strategy.features({'strategy_metadata': metadata}, {})['market_cap_krw'] == 250_000_000_000
    metadata['observed_at'] = '2026-06-05T10:00:00+09:00'
    assert strategy.features({'strategy_metadata': metadata}, {})['market_cap_krw'] is None


def test_two_valid_scopes_publish_atomically_and_preserve_ai(tmp_path):
    from src.tests.test_mechanistic_entry_runtime_policy import initial, source as initial_source
    from src.engine.scalping import ai_action_outcome_calibration as c
    initial(tmp_path)
    previous = runtime.publish(initial_source(tmp_path), data_root=tmp_path,
        adopt_all_continuous=True, adopt_hierarchy=True, now=datetime(2026,9,13,22,tzinfo=runtime.KST))
    selections = {}
    for scope in ['KRX|KRX_REGULAR', 'NXT|NXT_AFTERMARKET']:
        parent = runtime.for_cohort(previous, tuple(scope.split('|')))['machine_policy']
        item = candidate(parent)
        item['scope'] = scope.split('|')
        item['policy']['strategy']['scope'] = item['scope']
        item['policy_sha256'] = strategy.digest(item['policy'])
        selections[scope] = dict(candidate=item, promotion_pass=True)
    path = tmp_path/'multi.json'
    path.write_text(json.dumps(c._with_artifact_content_sha256(dict(target_date='2026-09-11',
        report_scope='main_mechanistic_entry', noncompact_sections_refreshed=True,
        strategy_refinements_by_scope=selections))))
    receipt = runtime.activate_strategy_report(path, data_root=tmp_path, now=datetime(2026,9,14,12,tzinfo=runtime.KST))
    assert receipt['scopes'] == sorted(selections)
    active = runtime.load_effective(data_root=tmp_path,target_date='2026-09-15')
    for scope in selections:
        old = runtime.for_cohort(previous, tuple(scope.split('|')))
        new = runtime.for_cohort(active, tuple(scope.split('|')))
        assert new['machine_policy'] == selections[scope]['candidate']['policy']
        assert new['ai_policy'] == old['ai_policy']


def test_successor_keeps_parent_missing_source_fallback():
    original = setup(); raw = deepcopy(original['strategy_raw_input'])
    raw['features'].pop('order_flow_pressure_score', None)
    parent = strategy._mutate_tree(policy(), {'tape_supportive_score':60}, None)
    successor = strategy._mutate_tree(parent, {'tape_supportive_score':64, 'ask_wall_ratio':7}, None)
    old, _ = strategy.select(parent, raw, original)
    new, receipt = strategy.select(successor, raw, original)
    assert old == new
    assert receipt['fallback_reason'] == 'source_missing_parent'


def test_machine_component_rollback_preserves_latest_ai(tmp_path):
    from src.tests.test_mechanistic_entry_runtime_policy import initial
    previous = initial(tmp_path)
    applied = runtime.activate_strategy_report(activation_source(tmp_path, candidate(previous['machine_policy'])),
        data_root=tmp_path, now=datetime(2026,9,14,12,tzinfo=runtime.KST))
    active = runtime.load_effective(data_root=tmp_path, target_date='2026-09-14')
    result = runtime.rollback_machine_component(previous['bundle_sha256'], data_root=tmp_path,
        now=datetime(2026,9,14,13,tzinfo=runtime.KST))
    restored = runtime.load_effective(data_root=tmp_path, target_date='2026-09-21')
    assert result['status'] == 'machine_component_rolled_back'
    assert restored['machine_policy'] == previous['machine_policy']
    assert restored['ai_policy'] == active['ai_policy']
    assert not runtime.validate_attempt_generation(applied['bundle_sha256'], data_root=tmp_path,
        now=datetime(2026,9,14,14,tzinfo=runtime.KST))['allowed']


def test_source_admission_uses_attempt_fallback_before_economic_selection():
    from src.engine.scalping import ai_action_outcome_calibration as c
    from src.tests.test_ai_action_outcome_calibration import _natural_refinement_fixture
    rows, receipt = _natural_refinement_fixture()
    for row in rows:
        row['scanner_promotion_id'] = None
    strict, _ = c._common_refinement_population([], rows, target_date=receipt['target_date'],
        source_receipt=receipt, paired_contract={})
    assert not strict
    admitted, contract = c._common_refinement_population([], rows, target_date=receipt['target_date'],
        source_receipt=receipt, paired_contract={}, allow_attempt_identity_fallback=True)
    assert len(admitted) == len(rows)
    assert contract['attempt_identity_fallback_count'] == len(rows)
    assert contract['input_row_disposition_complete']
    conflicting = deepcopy(rows[0]); conflicting['comparison']['entry_path_target_pct'] = 9
    admitted, contract = c._common_refinement_population([], rows+[conflicting], target_date=receipt['target_date'],
        source_receipt=receipt, paired_contract={}, allow_attempt_identity_fallback=True)
    assert len(admitted) == len(rows)-1
    assert contract['row_exclusion_reason_counts']['conflicting_exact_attempt'] == 2


def test_machine_rank_ignores_float_noise_before_episode_support():
    from src.engine.scalping.ai_action_outcome_calibration import _machine_admission_rank
    a = dict(win_rate_pct=100., selected_path_ev_pct=.10000000000000009,
             paired_admission_delta_pct=.1, selected_opportunity_count=1)
    b = {**a, 'selected_path_ev_pct':.1, 'selected_opportunity_count':2}
    assert _machine_admission_rank(b) > _machine_admission_rank(a)


@pytest.mark.parametrize('name', ['maximum_spread_bp', 'maximum_top3_ask_to_bid_ratio'])
def test_strategy_rejects_zero_execution_bounds_before_replay(name):
    from src.engine.scalping import entry_strategy_policy as strategy
    from src.engine.scalping.entry_setup_evidence import MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1
    policy = strategy.seed(MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1, ('KRX','KRX_REGULAR'))
    policy['strategy']['nodes']['root']['profile'][name] = 0.
    assert 'strategy_execution_threshold_must_be_positive' in strategy.validate(policy['strategy'])


@pytest.mark.parametrize('wins,count', [(6,10),(12,20),(18,30)])
def test_machine_supported_win_rate_outranks_one_lucky_entry(wins,count):
    from src.engine.scalping import entry_strategy_policy as mod
    single=dict(win_rate_pct=100.,selected_path_ev_pct=.1,paired_admission_delta_pct=.1,selected_opportunity_count=1)
    supported={**single,'win_rate_pct':100*wins/count,'selected_opportunity_count':count,'selected_path_ev_pct':-.4}
    assert mod.machine_admission_rank(supported)>mod.machine_admission_rank(single)


def test_machine_support_rank_keeps_negative_ev_and_episode_denominator():
    from src.engine.scalping import entry_strategy_policy as mod
    a=dict(win_rate_pct=60.,selected_path_ev_pct=-.4,paired_admission_delta_pct=-.2,selected_opportunity_count=20,selected_attempt_count=20)
    b={**a,'selected_attempt_count':200}
    assert mod.machine_admission_rank(a)==mod.machine_admission_rank(b)
    assert mod.machine_admission_rank({**a,'selected_path_ev_pct':-.3})>mod.machine_admission_rank(a)
    assert mod.machine_support_adjusted_win_rate({**a,'selected_opportunity_count':0}) is None
    assert mod.machine_support_adjusted_win_rate({**a,'win_rate_pct':101}) is None


def test_machine_selection_version_invalidates_old_rank_checkpoint(monkeypatch):
    from src.engine.scalping import ai_action_outcome_calibration as c
    one_research_candidate(monkeypatch)
    original=strategy.joint_candidates; calls=[]
    def count_search(*args, **kwargs):
        calls.append(kwargs.get('start'))
        yield from original(*args, **kwargs)
    monkeypatch.setattr(strategy,'joint_candidates',count_search)
    kwargs=dict(parent=evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1,scope=('KRX','KRX_REGULAR'),source_contract={},machine_policy_only=True)
    first=c.build_main_strategy_refinement([machine_cost_row()],**kwargs)
    monkeypatch.setattr(strategy,'MACHINE_SELECTION_VERSION','test-new-score-version')
    second=c.build_main_strategy_refinement([machine_cost_row()],previous=first,**kwargs)
    assert calls==[0,0]
    assert first['input_sha256']!=second['input_sha256']
    assert second['selection_basis']=='test-new-score-version'
    assert second['machine_evidence']['train']['economics']['support_adjusted_win_rate_pct']<100


def test_machine_conversion_promotion_preserves_existing_entries(monkeypatch):
    from src.engine.scalping import ai_action_outcome_calibration as c
    one_research_candidate(monkeypatch)
    parent=evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1; scope=('KRX','KRX_REGULAR')
    result=c.build_main_strategy_refinement([machine_cost_row()],parent=parent,scope=scope,source_contract={},machine_policy_only=True)
    candidate=deepcopy(result['candidate'])
    candidate['evidence']['train']['action_transition_counts']['ENTER_NOW->RECHECK']=15
    candidate['evidence_sha256']=strategy.digest(candidate['evidence'])
    assert 'train_machine_existing_entries_changed_without_evaluation' in strategy.promotion_errors(candidate,parent,scope)
    candidate['evidence']['train']['action_transition_counts'].pop('ENTER_NOW->RECHECK')
    candidate['evidence']['train']['action_transition_counts']['ENTER_NOW->ENTER_NOW']=15
    candidate['evidence_sha256']=strategy.digest(candidate['evidence'])
    assert not strategy.promotion_errors(candidate,parent,scope)


def test_preservation_rule_does_not_invalidate_already_published_legacy_policy(monkeypatch):
    from src.engine.scalping import ai_action_outcome_calibration as c
    one_research_candidate(monkeypatch)
    parent=evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1; scope=('KRX','KRX_REGULAR')
    result=c.build_main_strategy_refinement([machine_cost_row()],parent=parent,scope=scope,source_contract={},machine_policy_only=True)
    candidate=deepcopy(result['candidate'])
    candidate['evaluation_basis'] = 'machine_nonentry_opportunity_v1'
    candidate['preserve_existing_entries'] = True
    candidate['evidence']['train']['economics']['basis'] = 'nonentry_to_enter_now_cost_bound_quality_path'
    candidate['evidence']['train']['action_transition_counts']['ENTER_NOW->RECHECK']=1
    candidate['evidence_sha256']=strategy.digest(candidate['evidence'])
    assert strategy.promotion_errors(candidate,parent,scope,existing_publication=True)
    candidate.pop('preserve_existing_entries')
    assert strategy.promotion_errors(candidate,parent,scope)
    assert not strategy.promotion_errors(candidate,parent,scope,existing_publication=True)


def test_full_population_success_failure_neutral_and_fixed_denominator():
    from src.engine.scalping import ai_action_outcome_calibration as c
    rows = [machine_cost_row(), machine_cost_row('adverse_first'), machine_cost_row(), machine_cost_row()]
    for i, row in enumerate(rows):
        row['scanner_promotion_id'] = str(i)
        row['decision_trace_id'] = str(i)
        row['comparison']['incumbent_machine_action'] = 'ENTER_NOW' if i < 3 else 'BLOCK'
    rows[2]['entry_quality_path']['gross_net_target_pct'] = .2
    baseline = c._machine_admission_metrics(rows, ['ENTER_NOW'] * 3 + ['BLOCK'])
    result = c._machine_admission_metrics(rows, ['BLOCK', 'BLOCK', 'ENTER_NOW', 'ENTER_NOW'])
    assert result['comparable_population_sha256'] == baseline['comparable_population_sha256']
    assert result['comparable_opportunity_count'] == 4
    assert result['paired_admission_delta_pct'] == pytest.approx((-.3 + .7 + 0 + .3) / 4)
    assert result['win_rate_pct'] == 50
    assert result['selected_path_ev_pct'] == pytest.approx(.15)
    assert result['existing_success_retention_rate_pct'] == 0
    assert sum(result['transition_attempt_counts'].values()) == 4
    assert result['missed_success_simple_sum_path_pct'] == pytest.approx(.3)
    assert result['avoided_loss_simple_sum_path_pct'] == pytest.approx(.7)
    assert rows[0]['comparison']['incumbent_machine_action'] == 'ENTER_NOW'


def test_full_population_missing_existing_outcome_is_not_zero_or_changeable():
    from src.engine.scalping import ai_action_outcome_calibration as c
    row = machine_cost_row(None)
    row['comparison']['incumbent_machine_action'] = 'ENTER_NOW'
    result = c._machine_admission_metrics([row], ['BLOCK'])
    assert result['unevaluated_existing_entry_changes'] == [row['decision_trace_id']]
    assert result['paired_admission_delta_pct'] is None
    assert c._machine_admission_metrics([row], ['ENTER_NOW'])['unevaluated_existing_entry_changes'] == []
    with pytest.raises(ValueError, match='population_mismatch'):
        c._machine_admission_metrics([row], [])


def test_full_population_all_block_is_unranked_and_legacy_comparison_available():
    from src.engine.scalping import ai_action_outcome_calibration as c
    good, bad = machine_cost_row(), machine_cost_row('adverse_first')
    bad['comparison']['incumbent_machine_action'] = 'ENTER_NOW'
    full = c._machine_admission_metrics([good, bad], ['BLOCK', 'BLOCK'])
    assert full['paired_admission_delta_pct'] == pytest.approx(.35)
    assert strategy.machine_admission_rank(full)[0] is None
    legacy = c._machine_admission_metrics([good, bad], ['ENTER_NOW', 'BLOCK'], full_population=False)
    assert legacy['paired_admission_delta_pct'] == pytest.approx(.3)
    assert legacy['excluded_attempt_counts'] == {'outside_nonentry_population': 1}


def test_full_population_gate_rejects_mixed_basis_or_incumbent_population(monkeypatch):
    from src.engine.scalping import ai_action_outcome_calibration as c
    one_research_candidate(monkeypatch)
    parent = evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1; scope = ('KRX', 'KRX_REGULAR')
    candidate = c.build_main_strategy_refinement([machine_cost_row()], parent=parent, scope=scope,
        source_contract={}, machine_policy_only=True)['candidate']
    assert not strategy.promotion_errors(candidate, parent, scope)
    for key, value in [('selection_score_version', 'support_adjusted_win_rate_preserve_entries_v3'),
                       ('evaluation_basis', 'invalid')]:
        broken = deepcopy(candidate); broken[key] = value
        assert strategy.promotion_errors(broken, parent, scope)
    broken = deepcopy(candidate)
    broken['evidence']['incumbent_train']['economics']['comparable_population_sha256'] = '0' * 64
    broken['evidence_sha256'] = strategy.digest(broken['evidence'])
    assert 'strategy_machine_incumbent_population_mismatch' in strategy.promotion_errors(broken, parent, scope)


def test_full_population_parent_tie_is_retained(monkeypatch):
    from src.engine.scalping import ai_action_outcome_calibration as c
    one_research_candidate(monkeypatch)
    parent = research_policy()
    row = machine_cost_row()
    result = c.build_main_strategy_refinement([row], parent=parent, scope=('KRX','KRX_REGULAR'),
        source_contract={}, machine_policy_only=True)
    assert result['machine_policy'] == parent
    assert result['machine_evidence']['train']['economics']['paired_admission_delta_pct'] == 0


def test_full_population_can_select_loss_avoidance_without_new_entry(monkeypatch):
    from src.engine.scalping import ai_action_outcome_calibration as c
    parent = research_policy(); child = deepcopy(parent)
    child['strategy']['nodes']['root']['profile']['maximum_spread_bp'] = 20
    good, bad = machine_cost_row(), machine_cost_row('adverse_first')
    bad.update(decision_trace_id='loser', scanner_promotion_id='loser')
    def decide(source, *, policy):
        if source is bad['setup_evidence']:
            raise AssertionError('caller inputs should be frozen copies')
        losing = source.get('test_losing')
        return {'action': 'BLOCK' if losing and policy == child else 'ENTER_NOW'}
    bad['setup_evidence']['test_losing'] = True
    monkeypatch.setattr(c, 'mechanistic_entry_policy_decision', decide)
    monkeypatch.setattr(strategy, 'joint_candidates', lambda *a, **kw: iter([(child, {'cursor':1,'search_complete':True})]))
    result = c.build_main_strategy_refinement([good,bad], parent=parent, scope=('KRX','KRX_REGULAR'),
        source_contract={}, machine_policy_only=True)
    assert result['machine_policy'] == child
    assert result['promotion_pass'], result['promotion_errors']
    assert result['machine_evidence']['train']['action_transition_counts'] == {'ENTER_NOW->ENTER_NOW':1, 'ENTER_NOW->BLOCK':1}
    assert result['machine_evidence']['train']['economics']['paired_admission_delta_pct'] == pytest.approx(.35)


@pytest.mark.parametrize('dependency', ['source', 'parent', 'generation', 'current'])
def test_current_generation_cache_checks_every_dependency_and_isolates_callers(monkeypatch, tmp_path, dependency):
    from src.engine.scalping import ai_action_outcome_calibration as c
    from src.tests.test_mechanistic_entry_runtime_policy import initial
    previous = initial(tmp_path); one_research_candidate(monkeypatch)
    result = c.build_main_strategy_refinement([machine_cost_row()], parent=previous['machine_policy'],
        scope=('KRX','KRX_REGULAR'), source_contract={}, machine_policy_only=True)
    runtime.activate_strategy_report(activation_source(tmp_path, result['candidate']), data_root=tmp_path,
        now=datetime(2026,9,14,12,tzinfo=runtime.KST))
    active = runtime.load_effective(data_root=tmp_path, target_date='2026-09-22')
    original = runtime._read; reads = []
    monkeypatch.setattr(runtime, '_read', lambda p: (reads.append(str(p)), original(p))[1])
    cached = runtime.load_effective(data_root=tmp_path, target_date='2026-09-22')
    assert cached == active and not reads
    cached['machine_policy']['thresholds']['maximum_spread_bp'] = -1
    assert runtime.load_effective(data_root=tmp_path,target_date='2026-09-22') == active
    root = runtime.root(tmp_path)
    paths = {'source':root/'sources'/f"{active['source_file_sha256']}.json",
             'parent':root/'generations'/f"{active['strategy_activation']['parent_bundle_sha256']}.json",
             'generation':root/'generations'/f"{active['bundle_sha256']}.json", 'current':root/'current.json'}
    paths[dependency].write_text('{}')
    with pytest.raises((ValueError,KeyError)):
        runtime.load_effective(data_root=tmp_path,target_date='2026-09-22')
    assert reads


def test_scheduled_machine_report_retains_explicit_consumed_training_boundary(monkeypatch, tmp_path):
    from src.engine.scalping import ai_action_outcome_calibration as c
    from src.tests.test_mechanistic_entry_runtime_policy import initial
    initial(tmp_path)
    report_path = tmp_path/'report/ai_decision_action_outcome_calibration/machine_policy_2026-09-22.json'
    report_path.parent.mkdir(parents=True,exist_ok=True)
    report_path.write_text(json.dumps(c._with_artifact_content_sha256({'selections':{'KRX|KRX_REGULAR':{
        'training_through_date':'2026-09-22','holdout_boundary_basis':'explicit_forward_boundary'}}})))
    row=machine_cost_row();row['source_date']='2026-09-22'
    seen=[]
    monkeypatch.setattr(c,'_common_refinement_population',lambda *a,**kw:([row],{}))
    def build(*a,**kw):
        seen.append(kw['training_through_date'])
        return {'status':'source_gap'}
    monkeypatch.setattr(c,'build_main_strategy_refinement',build)
    c.build_machine_policy_report([row],source_receipt={},target_date='2026-09-22',data_root=tmp_path)
    assert seen == ['2026-09-22']
    with pytest.raises(ValueError,match='consumed_holdout'):
        c.build_machine_policy_report([row],source_receipt={},target_date='2026-09-22',data_root=tmp_path,
            training_through_date='2026-09-21')


def test_machine_replay_skips_only_unpriced_nonentry_and_preserves_input(monkeypatch):
    from src.engine.scalping import ai_action_outcome_calibration as c
    one_research_candidate(monkeypatch)
    good = machine_cost_row()
    missing = deepcopy(good)
    missing['decision_trace_id'] = 'missing'
    missing['comparison']['entry_cost_contract'] = {}
    frozen = deepcopy([good, missing])
    calls = []
    original = c.mechanistic_entry_policy_decision
    def counted(setup, *, policy):
        calls.append(policy)
        return original(setup, policy=policy)
    monkeypatch.setattr(c, 'mechanistic_entry_policy_decision', counted)
    result = c.build_main_strategy_refinement([good, missing],
        parent=evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1, scope=('KRX','KRX_REGULAR'),
        source_contract={}, machine_policy_only=True)
    assert [good, missing] == frozen
    assert len(calls) == 3  # Two incumbent replays, only one candidate replay.
    arm = result['machine_evidence']['train']
    assert arm['replay_coverage']['excluded_nonentry_count'] == 1
    assert arm['economics']['excluded_attempt_counts'] == {'full_cost_scope_mismatch': 1}
    assert arm['economics']['selected_path_ev_pct'] == pytest.approx(.3)
    assert arm['economics']['comparable_attempt_count'] == 1


def test_machine_replay_keeps_unpriced_existing_entry_promotion_guard(monkeypatch):
    from src.engine.scalping import ai_action_outcome_calibration as c
    one_research_candidate(monkeypatch)
    row = machine_cost_row()
    row['comparison']['entry_cost_contract'] = {}
    calls = []
    def decide(setup, *, policy):
        calls.append(policy)
        return dict(action='ENTER_NOW' if policy == evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1 else 'BLOCK')
    monkeypatch.setattr(c, 'mechanistic_entry_policy_decision', decide)
    result = c.build_main_strategy_refinement([row],
        parent=evidence.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1, scope=('KRX','KRX_REGULAR'),
        source_contract={}, machine_policy_only=True)
    assert len(calls) == 2
    assert result['promotion_pass'] is False
    assert result['machine_candidate_scores'][0]['economics']['unevaluated_existing_entry_changes'] == ['attempt-1']
