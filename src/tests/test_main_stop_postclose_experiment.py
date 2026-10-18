"""Normal publisher consumes real experiment producers and checks native rows."""
from dataclasses import asdict
import json

import pytest

from src.engine.automation import main_stop_postclose as post
from src.engine.scalping import main_stop_experiment as experiment
from src.engine.scalping import main_stop_policy as policy
from src.engine.scalping.main_stop_replay import candidates
from src.tests.test_main_stop_policy import baseline, publication, seal


def prepared(tmp_path, monkeypatch, *, observed_start_delta=0, mode='prospective'):
    _, report, parent, source = publication(tmp_path)
    base=1791766800.;value=baseline()
    params=dict(parent_sha256=policy.digest(asdict(value)),code_sha256=post.code_sha(),
        operator_lock_sha256=policy.digest([]),allowed_keys=['grace_sec'],
        max_daily_change={'grace_sec':60},split_at=base+500,embargo_sec=60.,min_train=2,min_holdout=2,
        minimum_paired_ev_krw=0.,max_censoring_ratio=0.,max_standard_error_krw=0.,
        candidate_grid={k:asdict(v) for k,v in candidates(value).items() if k=='parent' or k.startswith('grace_sec:')},
        source_start_at=base,source_end_at=base+1108,hypothesis='Fixed test comparison of a known adverse path.')
    monkeypatch.setattr(experiment,'_clock',lambda:base-100 if mode=='prospective' else base+1300)
    registered=experiment.register_experiment(tmp_path/'experiments',experiment_id='native-grace',revision=1,
        cell='SCANNER|REGULAR',parameters=params,mode=mode)
    # Gate fixture only; the separately executed research harness produces real
    # offline measurements and does not claim this unit fixture is live PASS.
    performance=dict(schema='main_stop_performance_v1',code_sha256=post.code_sha(),
        status='pass',scope='runtime_and_postclose',unresolved_findings=[])
    if mode=='historical_report_only':
        performance.update(status='measured',scope='offline_research_and_pure_decisions',
            allowed_runtime_apply=False,source_sha256=report['source_sha256'],metrics={'rows':36})
    measured=seal(tmp_path/'performance.json',performance)
    monkeypatch.setattr(experiment,'_clock',lambda:base+1400)
    contract=experiment.finalize_experiment(tmp_path/'experiments',registered,
        source_inventory=report['source_inventory'],performance_receipt=measured,
        observed_start_at=base+observed_start_delta,observed_end_at=base+1108)
    return report,parent,source,contract


def republish(tmp_path, report,parent,source,contract):
    completed=json.loads((tmp_path/'costs.json').read_text())['rows']
    return post.publish(tmp_path,'2026-10-12','2026-10-13',
        parents={f'{r}|{m}':baseline() for r in policy.ROLES for m in policy.MARKETS},
        parent_receipt=parent,source_paths=[source],snapshot_receipt=report['snapshot_receipt'],
        experiments={'SCANNER|REGULAR':contract},completed=completed,economic_sources=report['economic_sources'])


def test_v2_producer_contract_reaches_normal_publisher_and_exact_changed_cell(tmp_path,monkeypatch):
    report,parent,source,contract=prepared(tmp_path,monkeypatch)
    bundle,result=republish(tmp_path,report,parent,source,contract)
    assert bundle['cells']['SCANNER|REGULAR']['status']=='selected'
    assert bundle['cells']['SCANNER|REGULAR']['values']['grace_sec']==0
    assert sum(c['status']=='selected' for c in bundle['cells'].values())==1
    env,_=post.handoff(tmp_path,'2026-10-13')
    policy.preload(env)
    try:
        pin=policy.pin(position_key='target:999:005930',role='SCANNER',market='REGULAR',
            target='2026-10-13',baseline=baseline())
        assert policy.pin_values(pin,'target:999:005930').grace_sec==0
    finally:policy.preload({})


def test_claimed_source_bounds_cannot_replace_actual_consumed_position_bounds(tmp_path,monkeypatch):
    report,parent,source,contract=prepared(tmp_path,monkeypatch,observed_start_delta=1)
    before=post.committed_path(tmp_path,'2026-10-12').read_bytes()
    with pytest.raises(ValueError,match='observed_window_unverified'):
        republish(tmp_path,report,parent,source,contract)
    assert post.committed_path(tmp_path,'2026-10-12').read_bytes()==before


def test_historical_real_registration_has_no_normal_policy_publication_authority(tmp_path,monkeypatch):
    report,parent,source,contract=prepared(tmp_path,monkeypatch,mode='historical_report_only')
    before=post.committed_path(tmp_path,'2026-10-12').read_bytes()
    with pytest.raises(ValueError,match='historical_experiment_report_only'):
        republish(tmp_path,report,parent,source,contract)
    assert post.committed_path(tmp_path,'2026-10-12').read_bytes()==before
