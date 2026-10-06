from copy import deepcopy
from datetime import datetime
import math

import pytest

from src.engine.scalping import entry_admission_analysis as H
from src.engine.scalping import entry_admission_recipe as A
from src.engine.scalping import entry_setup_evidence as E
from src.tests.test_entry_strategy_policy import raw, setup, policy
from src.tests.test_entry_observation_recipe_policy import cost_path


def row_and_prices():
    row, _ = cost_path()
    row.update(effective_venue='KRX', session_bucket='KRX_REGULAR',
        outcome_stop_owner='mechanical_stop', outcome_stop_distance_pct=-1.,
        entry_quality_path={'exact_stop_distance_pct': -1.})
    row['comparison']['conservative_execution_cost_pct'] = .3
    row['decision_ts'] = '2026-09-29T09:00:00+09:00'
    start = datetime.fromisoformat(row['decision_ts']).timestamp()
    row['setup_evidence']['strategy_raw_input']['entry_machine_input_as_of'] = start
    row['setup_evidence']['strategy_raw_sha256'] = H.S.digest(row['setup_evidence']['strategy_raw_input'])
    bars = [dict(t=start + i * 60, open=100., high=100.1, low=99.9, close=100.) for i in range(1, 61)]
    return row, bars


def test_late_rise_extends_timeout_but_never_overwrites_earlier_stop():
    row, bars = row_and_prices()
    bars[19]['high'] = 100.5
    assert H.path(row, bars, seconds=600)['status'] == 'timeout'
    late = H.path(row, bars, seconds=3600)
    assert late['status'] == 'target' and late['delay_sec'] == 1200
    obs = dict(trace=row['decision_trace_id'], day=row['source_date'], symbol=row['stock_code'],
        ts=row['decision_ts'], raw_sha256=row['setup_evidence']['strategy_raw_sha256'],
        cost_contract_sha256=H.S.digest(row['comparison']['entry_cost_contract']), path=late)
    assert H.native_path_value(row, obs) == (.1, 'net_target_first', None)
    bars[2]['low'] = 98.9
    assert H.path(row, bars, seconds=3600)['status'] == 'stop'


@pytest.mark.parametrize('damage', ['gap', 'both', 'partial', 'future', 'naive', 'cost', 'stop', 'nan'])
def test_uncertain_path_does_not_become_a_winner(damage):
    row, bars = row_and_prices()
    bars[19]['high'] = 101
    if damage == 'gap': bars.pop(1)
    elif damage == 'both': bars[19]['low'] = 98
    elif damage == 'partial':
        row['decision_ts'] = '2026-09-29T09:00:30+09:00'
        row['setup_evidence']['strategy_raw_input']['entry_machine_input_as_of'] += 30
        bars[0]['high'] = 101
    elif damage == 'future': row['setup_evidence']['strategy_raw_input']['entry_machine_input_as_of'] += 1
    elif damage == 'naive': row['decision_ts'] = '2026-09-29T09:00:00'
    elif damage == 'cost': row['comparison']['conservative_execution_cost_pct'] = 0
    elif damage == 'stop': row['outcome_stop_distance_pct'] = -.5
    elif damage == 'nan': bars[1]['high'] = math.nan
    result = H.path(row, bars, seconds=3600)
    assert result['status'] not in {'target', 'stop', 'timeout'} and result['net_pct'] is None


def test_parent_recheck_promotion_preserves_original_facts_and_ai_veto():
    payload = raw()
    payload.update(stock_code='000660')
    payload['current']['fluctuation_pct'] = 1
    payload['features'].update(curr_vs_micro_vwap_bp=-5, curr_vs_ma5_bp=0, micro_vwap_available=True)
    original = setup(payload)
    parent = policy()
    candidate = A.candidate_policy(parent)
    before = deepcopy(original)
    old = E.mechanistic_entry_policy_decision(original, policy=parent)
    new = E.mechanistic_entry_policy_decision(original, policy=candidate)
    assert old['action'] == 'RECHECK' and new['action'] == 'ENTER_NOW'
    assert new['core_comparison'] == old['core_comparison'] and original == before
    assert new['strategy_selection']['policy_sha256'] == H.S.digest(candidate)
    assert not E.validate_entry_setup_evidence(new['effective_setup_evidence'])
    frozen = deepcopy(new['effective_setup_evidence'])
    new['strategy_selection']['diagnostic_after_capture'] = True
    assert new['effective_setup_evidence'] == frozen
    # The live compact screen consumes the already selected effective setup,
    # unlike the offline comparison that started from the unselected parent.
    from src.tests.test_ai_engine_openai_transport import _build_engine
    from src.engine.scalping import mechanistic_entry_runtime_policy as M
    from src.tests.test_entry_setup_evidence import _risk
    normalized = _build_engine()._normalize_entry_setup_v2_14_result(
        _risk('PASS', ['NO_BLOCKING_RISK'],
              support=['clean_continuation_probe_eligible'], contradict=['trigger_confirmation_missing']),
        exact_payload=payload, setup_evidence=frozen,
        live_policy=dict(enabled=True, status='active_bounded_krx_canary',
            selected_prompt_version=M.AI_VERSION,
            primary_decision_owner='mechanistic_entry_adjudicator',
            ai_role='auxiliary_risk_screen_pass_veto_no_promotion',
            mechanistic_threshold_policy=candidate), prompt_version=M.AI_VERSION)
    assert normalized['decision_quality_contract_status'] != 'semantic_rejected'
    assert normalized['entry_mechanistic_action'] == 'ENTER_NOW'
    assert normalized['entry_ai_screen_status'] == 'pass'
    composed = E.compose_mechanistic_primary_decision(setup_evidence=original,
        ai_risk_adjudication=None, policy=candidate)
    assert composed['entry_mechanistic_action'] == 'ENTER_NOW'
    assert composed['action'] == 'WAIT' and not composed['entry_probe_intent']
    from src.tests.test_entry_setup_evidence import _risk
    pass_response = _risk('PASS', ['NO_BLOCKING_RISK'],
        support=['clean_continuation_probe_eligible'], contradict=['trigger_confirmation_missing'])
    accepted = E.compose_mechanistic_primary_decision(setup_evidence=original,
        ai_risk_adjudication=pass_response, policy=candidate)
    assert accepted['entry_probe_intent'] and accepted['entry_ai_screen_pass']
    # Exposure remains an intent consumed by the existing final submit guards.
    assert accepted['action'] == 'WAIT'
    veto = {**pass_response, 'risk_verdict':'VETO', 'risk_codes':['CONFIRMATION_MISSING']}
    rejected = E.compose_mechanistic_primary_decision(setup_evidence=original,
        ai_risk_adjudication=veto, policy=candidate)
    assert not rejected['entry_probe_intent']
    payload['stock_code'] = '005930'
    samsung = setup(payload)
    assert E.mechanistic_entry_policy_decision(samsung, policy=candidate)['action'] == E.mechanistic_entry_policy_decision(samsung, policy=parent)['action']


@pytest.mark.parametrize('field,value', [('buy_pressure_10t', 59.99), ('buy_pressure_10t', 100.01),
    ('net_aggressive_delta_10t', 0), ('tick_aggressor_trusted_count', 9),
    ('curr_vs_micro_vwap_bp', .01), ('tick_context_stale', True), ('quote_stale', True)])
def test_common_recipe_cannot_promote_missing_frozen_condition(field, value):
    payload = raw()
    payload.update(stock_code='000660')
    payload['current']['fluctuation_pct'] = 1
    payload['features'].update(curr_vs_micro_vwap_bp=-5, curr_vs_ma5_bp=0, micro_vwap_available=True)
    payload['features'][field] = value
    assert E.mechanistic_entry_policy_decision(setup(payload), policy=A.candidate_policy(policy()))['action'] != 'ENTER_NOW'


def test_action_union_report_keeps_unknowns_and_native_identity_separate(monkeypatch, tmp_path):
    from src.engine.scalping import ai_action_outcome_calibration as C
    row, bars = row_and_prices()
    payload = raw()
    payload.update(stock_code=row['stock_code'], entry_machine_input_as_of=datetime.fromisoformat(row['decision_ts']).timestamp())
    payload['quote'] = {'best_ask': 100}
    payload['features'].update(curr_vs_micro_vwap_bp=-5, curr_vs_ma5_bp=0, micro_vwap_available=True)
    payload['current']['fluctuation_pct'] = 1
    row.update(setup_evidence=setup(payload), outcome_request_code='000660', bundle_sha256='b' * 64)
    bars[19]['high'] = 100.5
    monkeypatch.setattr(C, '_machine_source_contract_valid', lambda _: True)
    key = (row['source_date'], row['stock_code'], 'KRX', 'KRX_REGULAR', '000660')
    monkeypatch.setattr(H, 'price_index', lambda *args: ({key: bars}, [], []))
    result = H.build_report([row], parent=policy(), target_date='2026-10-02', data_root=tmp_path)
    observation = result['observations'][0]
    assert observation['path_10m']['status'] == 'timeout' and observation['path']['status'] == 'target'
    assert observation['native_provenance'] is None
    assert result['groups']['non_samsung']['native_observation_count'] == 0
    assert result['groups']['non_samsung']['comparison']['candidate']['selected_observation_count'] == 1
    H.validate_report(result, parent=policy(), target_date='2026-10-02', require_files=True)
    altered = deepcopy(result)
    altered['pristine_holdout'] = True
    altered['artifact_content_sha256'] = H.S.digest({k:v for k,v in altered.items() if k != 'artifact_content_sha256'})
    with pytest.raises(ValueError, match='contract_invalid'):
        H.validate_report(altered, parent=policy(), target_date='2026-10-02')


def test_recipe_generator_selects_new_observation_holdout_without_winner_retention(monkeypatch, tmp_path):
    from src.engine.scalping import ai_action_outcome_calibration as C
    from src.engine.scalping import mechanistic_entry_runtime_policy as M
    parent = policy()
    parent['entry_situation_veto'] = C._winrate_veto_payload(68.75)
    monkeypatch.setattr(M, 'load_effective', lambda **kw: {'bundle_sha256':'b' * 64})
    monkeypatch.setattr(M, 'for_cohort', lambda *args: {'machine_policy':parent})
    monkeypatch.setattr(C, '_common_refinement_population', lambda _p, rows, **kw: (rows, {'row_exclusion_reason_counts':{}}))
    monkeypatch.setattr(H.S, 'completed_bar_rows', lambda *args, **kw: [])
    monkeypatch.setattr(C, 'mechanistic_entry_policy_decision', lambda s, *, policy: {
        'action': 'ENTER_NOW' if 'entry_admission_recipe' not in policy or s['strategy_raw_input']['features']['buy_pressure_10t'] >= 60 else 'RECHECK'})
    monkeypatch.setattr(H, 'native_path_value', lambda row, _: (.1 if row['win'] else -1., 'net_target_first' if row['win'] else 'exact_stop_first', None))
    rows = []
    for day, size, selected, wins, removed_wins in [('2026-09-29', 100, 60, 55, 5), ('2026-10-06', 30, 20, 18, 1)]:
        for i in range(size):
            payload = {'features':dict(buy_pressure_10t=65 if i < selected else 50, curr_vs_micro_vwap_bp=-5, micro_vwap_available=True, minute_candle_window_fresh=True)}
            rows.append(dict(source_date=day, stock_code=f'{i+1:06}', scanner_promotion_id=f'{day}-{i}',
                decision_trace_id=f'{day}-{i}', decision_ts=f'{day}T09:{i//60:02}:{i%60:02}+09:00',
                effective_venue='KRX', session_bucket='KRX_REGULAR',
                setup_evidence=dict(strategy_raw_input=payload, strategy_raw_sha256=H.S.digest(payload)),
                win=i < wins or selected <= i < selected + removed_wins))
    analysis = H.build_report([], parent=parent, target_date='2026-10-06', data_root=tmp_path)
    analysis['observations'] = [dict(trace=r['decision_trace_id'], day=r['source_date'],
        symbol=r['stock_code'], ts=r['decision_ts'], group='non_samsung', scope=['KRX','KRX_REGULAR'],
        raw_sha256=r['setup_evidence']['strategy_raw_sha256'], outcome_request_code='fixture',
        source_bundle_sha256='b' * 64, source_lane='observation', native_provenance=None,
        parent_action='ENTER_NOW', candidate_action='ENTER_NOW' if
            r['setup_evidence']['strategy_raw_input']['features']['buy_pressure_10t'] >= 60 else 'RECHECK',
        path=dict(status='target' if r['win'] else 'stop', net_pct=.1 if r['win'] else -1., delay_sec=60)) for r in rows]
    analysis['artifact_content_sha256'] = H.S.digest({k:v for k,v in analysis.items() if k != 'artifact_content_sha256'})
    report = C.build_winrate_policy_report(rows, source_receipt={'target_date':'2026-10-06'},
        target_date='2026-10-06', data_root=tmp_path, publication_day='2026-10-06',
        admission_recipe_id=A.RECIPE_ID, admission_analysis=analysis)
    assert report['disposition'] == 'successor_selected', report['hurdle_errors']
    assert report['holdout_dates'] == ['2026-10-06'] and report['candidate_threshold_bp'] is None
    assert report['success_retention_diagnostics']['holdout']['excluded_wins'] == 1
    assert report['candidate']['train']['native_selected_count'] == 0
    assert M._winrate_successor_hurdles_valid(report)
    assert not M._winrate_successor_hurdles_valid({**report, 'holdout_dates':['2026-10-02']})
