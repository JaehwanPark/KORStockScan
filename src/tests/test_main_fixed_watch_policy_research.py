"""Offline research contracts do not create native support or policy authority."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.engine.monitoring import main_fixed_watch_policy_research as research
from src.tests.test_entry_strategy_policy import policy


def freeze(tmp_path, rows=()):
    path = tmp_path/'retained.json'
    path.write_text(json.dumps(dict(rows=list(rows))))
    return research.freeze(policy(), [path], source_date='2026-10-06', publication_date='2026-10-06', target_date='2026-10-07')


def row(day='2026-10-02', trace='trace', admission='admission', origin='MAIN_FIXED_WATCH'):
    return dict(stock_code='034020',source_date=day,decision_ts=f'{day}T09:10:00+09:00',decision_trace_id=trace,
        effective_venue='KRX',session_bucket='KRX_REGULAR',watch_origin=origin,watch_admission_id=admission,
        watch_generation_id=f'g-{day}',scanner_promotion_id='scanner',setup_evidence={},source_provenance_verified=True)


def safe_replay(monkeypatch):
    monkeypatch.setattr(research.replay.calibration,'_machine_source_contract_valid',lambda r: r.get('source_provenance_verified') is True)
    monkeypatch.setattr(research.replay.calibration,'_machine_path_value',lambda r: (None,'missing_cost') if r.get('missing_cost') else (1,'target_first'))
    monkeypatch.setattr(research.replay,'decision_vector',lambda rows, policy: ['BLOCK']*len(rows))
    monkeypatch.setattr(research.replay,'economy',lambda rows, actions: dict(selected_opportunity_count=0,win_rate_pct=None))


def test_ten_candidates_are_frozen_before_outcomes_and_initial_designation_is_independent(tmp_path):
    frozen=freeze(tmp_path)
    assert len(frozen['candidates']) == len({r['id'] for r in frozen['candidates']}) == 10
    assert frozen['initial_policy_preproof_required'] is False
    result=research.evaluate(frozen)
    assert result['selection_status'] == 'source_gap'
    assert result['entry_runtime_eligible'] is True  # operator designation, not evidence
    assert result['candidate_policy_sha256'] is None
    assert result['allowed_runtime_apply'] is False
    assert result['actual_completed_net_profit_krw'] is None


@pytest.mark.parametrize('damage',['source','candidate','parent','kernel','authority','date'])
def test_frozen_contract_cannot_be_changed(tmp_path,damage):
    frozen=freeze(tmp_path)
    if damage=='source':Path(frozen['source_manifest'][0]['path']).write_text('{}')
    if damage=='candidate':frozen['candidates'][1]['policy']['strategy']['nodes'].clear()
    if damage=='parent':frozen['parent_policy_sha256']='f'*64
    if damage=='kernel':frozen['kernel_sha256']='f'*64
    if damage=='authority':frozen['allowed_runtime_apply']=True
    if damage=='date':frozen['target_date']='2026-10-06'
    with pytest.raises(ValueError):research.evaluate(frozen)


def test_repeats_scanner_episode_and_missing_cost_are_not_native_support(tmp_path,monkeypatch):
    safe_replay(monkeypatch)
    first=row()
    later={**row(trace='later'),'decision_ts':'2026-10-02T09:11:00+09:00'}
    scanner=row(trace='scanner',origin='ZERO_BASE_DISCOVERY')
    episode=row(trace='episode',origin='EPISODE')
    absent={**row(trace='cost',admission='different'),'missing_cost':True}
    result=research.evaluate(freeze(tmp_path,[first,first,later,scanner,episode,absent]))
    assert result['native_support'] == dict(fixed_watch_opportunities=1,scanner_diagnostic_opportunities=1)
    assert result['census']['duplicate_rows']==1
    assert result['exclusions']['non_main_watch_origin']==1
    assert result['exclusions']['cost_or_path_unresolved:missing_cost']==1
    assert result['selection_status']=='insufficient_sample'


def test_conflicting_trace_excludes_entire_admission(tmp_path,monkeypatch):
    safe_replay(monkeypatch)
    first=row()
    changed={**first,'setup_evidence':dict(changed=True)}
    result=research.evaluate(freeze(tmp_path,[first,changed,row(trace='later')]))
    assert result['native_support']['fixed_watch_opportunities']==0
    assert result['exclusions']['duplicate_trace_conflict']==1


def test_holdout_cannot_choose_a_training_runner_up(tmp_path,monkeypatch):
    safe_replay(monkeypatch)
    frozen=freeze(tmp_path,[row('2026-10-02'),row('2026-10-06')])
    ids={research.strategy.digest(c['policy']):i for i,c in enumerate(frozen['candidates'])}
    monkeypatch.setattr(research.replay,'decision_vector',lambda rows,p:ids[research.strategy.digest(p)])
    def score(rows,index):
        train=rows[0]['source_date']=='2026-10-02'
        rate=50 if index==0 else (90 if index==1 and train else 40 if index==1 else 80)
        return dict(selected_opportunity_count=10,win_rate_pct=rate)
    monkeypatch.setattr(research.replay,'economy',score)
    monkeypatch.setattr(research.strategy,'machine_winrate_improves',lambda a,b:a['win_rate_pct']>b['win_rate_pct'])
    monkeypatch.setattr(research.strategy,'machine_admission_rank',lambda a:a['win_rate_pct'])
    result=research.evaluate(frozen)
    assert result['training_scope']==['2026-10-02']
    assert result['validation_scope']==['2026-10-06']
    assert result['selection_status']=='measured_no_improvement'
    assert result['candidate_policy_sha256'] is None


def test_report_readback_binds_frozen_candidate_and_never_claims_actual_profit(tmp_path):
    frozen=freeze(tmp_path)
    path=tmp_path/'frozen.json'; path.write_text(json.dumps(frozen))
    result=research.evaluate(frozen)
    result.update(frozen_contract_path=str(path),frozen_contract_sha256=research.file_sha(path))
    result['report_sha256']=research.strategy.digest(result)
    assert research.validate_report(result,source_date='2026-10-06') is result
    result['actual_completed_net_profit_krw']=100
    result['report_sha256']=research.strategy.digest({k:v for k,v in result.items() if k!='report_sha256'})
    with pytest.raises(ValueError,match='authority'):research.validate_report(result,source_date='2026-10-06')


def test_postclose_consumer_uses_source_day_not_next_application_day(tmp_path):
    from src.engine.automation import postclose_summary_handoff as handoff
    from src.engine.automation.postclose_recommendation_intake import _report_date
    frozen=freeze(tmp_path)
    path=tmp_path/'frozen.json';path.write_text(json.dumps(frozen))
    result=research.evaluate(frozen)
    result.update(frozen_contract_path=str(path),frozen_contract_sha256=research.file_sha(path))
    result['report_sha256']=research.strategy.digest(result)
    assert _report_date(result)=='2026-10-06'
    report_dir=tmp_path/'report'
    target=handoff.stage_artifacts(report_dir,'2026-10-06','main_machine_policy')['main_fixed_watch_policy_research']
    target.parent.mkdir(parents=True);target.write_text(json.dumps(result))
    for symbol in ("403870", "196170", "036930"):
        child=research.freeze(policy(), [], source_date="2026-10-06", publication_date="2026-10-06", target_date="2026-10-07", symbol=symbol)
        fp=tmp_path/(symbol+".json");fp.write_text(json.dumps(child))
        outcome=research.evaluate(child);outcome.update(frozen_contract_path=str(fp),frozen_contract_sha256=research.file_sha(fp))
        outcome["report_sha256"]=research.strategy.digest(outcome)
        childpath=handoff.stage_artifacts(report_dir,"2026-10-06","main_machine_policy")["main_fixed_watch_policy_research_"+symbol]
        childpath.write_text(json.dumps(outcome))
    errors=handoff._stage_output_issues(report_dir,'2026-10-06','main_machine_policy')
    assert not any('main_fixed_watch' in error or 'fixed_watch_research' in error for error in errors)
    commands=handoff.stage_commands('main_machine_policy','2026-10-06','2026-10-06',recovery=True)
    assert len(commands)==4 and commands[0][2]=='src.engine.monitoring.main_fixed_watch_policy_research'
    assert handoff.stage_commands('main_machine_policy','2026-10-02','2026-10-02',recovery=True)==[]


def test_candidate_mutation_rebinds_non_samsung_recipe_parent(tmp_path):
    from src.engine.scalping.entry_admission_recipe import candidate_policy
    from src.engine.scalping.entry_setup_evidence import validate_mechanistic_entry_threshold_policy
    parent=candidate_policy(policy())
    frozen=research.freeze(parent, [],source_date="2026-10-06",publication_date="2026-10-06",target_date="2026-10-07",symbol="403870")
    for definition in frozen["candidates"]:
        assert validate_mechanistic_entry_threshold_policy(definition["policy"]) == []
        recipe=definition["policy"]["entry_admission_recipe"]
        assert recipe["parameters"] == parent["entry_admission_recipe"]["parameters"]
        assert recipe["symbol_predicate"] == "exclude_005930"
