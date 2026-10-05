from copy import deepcopy
import json

import pytest

from src.engine.scalping import samsung_absorption_acceptance_research as A
from src.engine.scalping import entry_first_signal_exit_research as E
from src.tests.test_entry_observation_recipe_policy import observation
from src.tests.test_entry_strategy_policy import policy


def row(trace='one', **kwargs):
    value = observation(trace=trace, symbol='005930', **kwargs)
    value.update(group='samsung',outcome_request_code='005930_AL',source_bundle_sha256='b'*64)
    return value


def test_samsung_adapter_preserves_identity_and_first_signal_ignores_labels():
    rows = [row(status='stop'), row('two',ts='2026-09-29T09:02:00+09:00')]
    with pytest.raises(ValueError, match='non_samsung_scope'):
        E.first_signal_events(rows)
    result = A.research(rows)['cohorts']['all_origins']
    assert result['original_nonoverlap']['candidate']['selected_observation_count'] == 2
    assert result['first_signal_nonoverlap']['candidate']['selected_ids'] == ['one']
    altered = deepcopy(rows)
    altered[0]['path'],altered[1]['path'] = altered[1]['path'],altered[0]['path']
    assert A.research(altered)['cohorts']['all_origins']['event_manifest'] == result['event_manifest']
    rows[0]['symbol'] = '000660'
    with pytest.raises(ValueError):
        A.research(rows)


def test_timeout_binary_and_positive_outcomes_are_separate():
    rows = [row(status='timeout', candidate='RECHECK'),
        row('two',ts='2026-09-29T10:01:00+09:00',status='stop',parent='RECHECK')]
    rows[0]['path'].update(net_pct=.04,delay_sec=3600)
    out = A.compare(rows)
    assert out['conclusions'] == dict(boundary_win_rate_pct='not_identifiable',
        target_with_timeout_rate_pct='no_improvement',positive_path_rate_pct='no_improvement')
    assert out['parent']['date_equal_metrics']['boundary_win_rate_pct'] is None
    assert out['parent']['date_equal_metrics']['positive_path_rate_pct'] == 100


def test_fixed_watch_population_uses_original_native_provenance():
    rows = [row(), row('two',ts='2026-09-29T10:01:00+09:00')]
    rows[0]['native_provenance'] = [rows[0]['day'],'005930','KRX','KRX_REGULAR','MAIN_FIXED_WATCH','admission','generation']
    report = A.research(rows)
    assert report['cohorts']['all_origins']['observation_count'] == 2
    assert report['cohorts']['fixed_watch']['observation_count'] == 1


def test_forward_frozen_waiting_and_tamper(tmp_path):
    evidence = tmp_path/'evidence.json'
    evidence.write_text('{}')
    frozen = A.freeze(policy(), [evidence])
    A.validate_frozen(frozen)
    waiting = A.prepare(tmp_path,'2026-10-06',frozen)
    assert waiting['status'] == 'waiting_new_source_date'
    assert not waiting['data_collected'] and not waiting['policy_selected']
    for field,value in [('recipe_id','other'),('later_source_after_date','2026-10-02'),
                        ('runtime_effect',True),('comparison_objectives',[])]:
        with pytest.raises(ValueError):
            A.prepare(tmp_path,'2026-10-06',A.seal({**frozen,field:value}))
    with pytest.raises(ValueError,match='forward_date'):
        A.prepare(tmp_path,'2026-10-02',frozen)
    evidence.write_text('{"changed":true}')
    with pytest.raises(ValueError):
        A.validate_frozen(frozen)


def test_forward_capture_intake_valid_and_changed_parent(tmp_path,monkeypatch):
    from src.tests.test_entry_admission_analysis import row_and_prices
    from src.engine.scalping import ai_action_outcome_calibration as C
    from src.engine.scalping import mechanistic_entry_runtime_policy as M
    source,bars = row_and_prices()
    source.update(source_date='2026-10-06', decision_ts='2026-10-06T09:00:00+09:00',stock_code='005930',
        bundle_sha256='b'*64,machine_action='RECHECK',outcome_request_code='005930_AL')
    source['comparison']['entry_cost_contract']['source_date']='2026-10-06'
    raw=source['setup_evidence']['strategy_raw_input']
    raw.update(stock_code='005930',effective_venue='KRX',session_bucket='KRX_REGULAR',
        entry_machine_input_as_of=A.H.datetime.fromisoformat(source['decision_ts']).timestamp())
    source['setup_evidence']['strategy_raw_sha256']=A.S.digest(raw)
    shift=7*86400
    for bar in bars:bar['t']+=shift
    capture=tmp_path/'data/report/machine_observation_projection/machine_observation_projection_2026-10-06_0_1.json'
    capture.parent.mkdir(parents=True)
    capture.write_text(json.dumps({'rows':[source]}))
    prices=tmp_path/'data/report/machine_completed_price_source/machine_completed_price_source_2026-10-06.json'
    prices.parent.mkdir(parents=True);prices.write_text('{}')
    evidence=tmp_path/'evidence.json';evidence.write_text('{}')
    frozen=A.freeze(policy(),[evidence])
    monkeypatch.setattr(M,'load_effective',lambda **kw:{'bundle_sha256':'b'*64})
    monkeypatch.setattr(M,'for_cohort',lambda *args:{'machine_policy':policy()})
    monkeypatch.setattr(C,'_machine_source_contract_valid',lambda r:True)
    monkeypatch.setattr(A.H,'price_index',lambda *args:({('2026-10-06','005930','KRX','KRX_REGULAR','005930_AL'):bars},[],[]))
    monkeypatch.setattr(A.F,'evaluate',lambda *args,**kw:dict(source_valid=True,parent_action='RECHECK',proposed_action='ENTER_NOW'))
    from src.engine.scalping import samsung_policy_compatibility as compatibility
    monkeypatch.setattr(compatibility,'source_bundle',lambda *a,**kw:dict(bundle_sha256='b'*64))
    out=A.prepare(tmp_path,'2026-10-06',frozen)
    assert out['status']=='evaluated'
    assert out['observations'][0]['path']['status']=='timeout'
    assert out['observations'][0]['path']['net_pct']==pytest.approx(-.3)
    monkeypatch.setattr(A.F,'evaluate',lambda *args,**kw:dict(source_valid=False))
    assert A.prepare(tmp_path,'2026-10-06',frozen)['status']=='source_quality_excluded_all'
    monkeypatch.setattr(M,'for_cohort',lambda *args:{'machine_policy':{}})
    with pytest.raises(ValueError,match='parent_changed'):
        A.prepare(tmp_path,'2026-10-06',frozen)
