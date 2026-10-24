import pytest
from src.engine.infrastructure.research_release_transition import Transition,assert_readable


def prepared(root,identity='case'):
    paths=[root/'data/runtime/runtime_release_selection.json',root/'data/threshold_cycle/pointer.json',
        root/'data/report/summary.json',root/'docs/checklists/next.md']
    transition=Transition(root,identity)
    for i,path in enumerate(paths):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(f'old-{i}'.encode())
        transition.add(path,f'new-{i}'.encode())
    return transition,paths


@pytest.mark.parametrize('boundary',['after_rename','after_record'])
@pytest.mark.parametrize('index',range(4))
def test_every_publication_boundary_recovers_the_entire_set(tmp_path,boundary,index):
    transition,paths=prepared(tmp_path)
    def fault(path,where):
        if path==paths[index] and where==boundary:raise RuntimeError('injected')
    with transition.owner():
        with pytest.raises(RuntimeError,match='injected'):transition.publish(verify=lambda:None,fault=fault)
    with pytest.raises(ValueError,match='incomplete'):assert_readable(tmp_path/'data')
    restored=Transition(tmp_path,'case')
    with restored.owner():restored.rollback(verify_before=lambda:None)
    assert [p.read_bytes() for p in paths]==[f'old-{i}'.encode() for i in range(4)]
    assert_readable(tmp_path/'data')


def test_resume_after_rename_and_external_successor_cas(tmp_path):
    transition,paths=prepared(tmp_path)
    def fault(path,where):raise RuntimeError('injected')
    with transition.owner():
        with pytest.raises(RuntimeError):transition.publish(verify=lambda:None,fault=fault)
    resumed=Transition(tmp_path,'case')
    with resumed.owner():resumed.publish(verify=lambda:assert_readable(tmp_path/'data'))
    assert [p.read_bytes() for p in paths]==[f'new-{i}'.encode() for i in range(4)]
    paths[1].write_bytes(b'another-writer')
    with resumed.owner():
        with pytest.raises(ValueError,match='rollback_cas'):resumed.rollback(verify_before=lambda:None)
    assert paths[0].read_bytes()==b'new-0' and paths[1].read_bytes()==b'another-writer'


def test_new_preparation_cannot_hide_an_incomplete_transition(tmp_path):
    first,paths=prepared(tmp_path)
    with first.owner():
        with pytest.raises(RuntimeError):first.publish(verify=lambda:(_ for _ in ()).throw(RuntimeError()))
    second=Transition(tmp_path,'other')
    with pytest.raises(ValueError,match='other_publication_incomplete'):second.add(tmp_path/'data/runtime/new',b'x')
    with pytest.raises(ValueError,match='incomplete'):assert_readable(tmp_path/'data')


@pytest.mark.parametrize('boundary',['after_rename','after_record'])
@pytest.mark.parametrize('index',range(6))
def test_real_metadata_writers_use_one_dynamic_journal_and_restore_all(tmp_path,monkeypatch,index,boundary):
    from src.engine import runtime_approval_summary as summary
    monkeypatch.setattr(summary, 'DATA_DIR', tmp_path/'data')
    monkeypatch.setattr(summary, 'REPORT_DIR', tmp_path/'data/report/runtime_approval_summary')
    summary_write = summary._atomic_write
    from src.engine.build_next_stage2_checklist import _atomic_write_checklist
    from src.engine.verify_threshold_cycle_postclose_chain import _atomic_write as strict_write
    from src.engine.automation.runtime_policy_bootstrap import _publish
    from src.engine.scalping.pre_submit_delay_initial_policy import _atomic
    transition=Transition(tmp_path,'dynamic')
    paths=[tmp_path/'data/runtime/runtime_release_selection.json',tmp_path/'data/threshold_cycle/policy.json',
        summary.summary_paths('2026-10-23')[0],tmp_path/'docs/checklists/next.md',
        tmp_path/'data/report/strict.json',tmp_path/'data/runtime/prepared/latest.json']
    for path in paths:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'old')
    steps=[lambda:_atomic(paths[0],{'release':'new'}),lambda:_atomic(paths[1],{'policy':'new'}),
        lambda:summary_write(paths[2],'new'),lambda:_atomic_write_checklist(paths[3],'new'),
        lambda:strict_write(paths[4],'new'),lambda:_publish(paths[5],'new')]
    def fault(path,where):
        if path==paths[index] and where==boundary:raise RuntimeError('injected')
    with transition.owner():
        with pytest.raises(RuntimeError,match='injected'):transition.execute(steps,verify=lambda:None,fault=fault)
    with pytest.raises(ValueError,match='incomplete'):assert_readable(tmp_path/'data')
    recovered=Transition(tmp_path,'dynamic')
    with recovered.owner():recovered.rollback(verify_before=lambda:None)
    assert all(path.read_bytes()==b'old' for path in paths)


def test_dynamic_journal_multiple_writes_resume_and_unknown_writer_cas(tmp_path,monkeypatch):
    from src.engine import runtime_approval_summary as summary
    monkeypatch.setattr(summary, 'DATA_DIR', tmp_path/'data')
    monkeypatch.setattr(summary, 'REPORT_DIR', tmp_path/'data/report/runtime_approval_summary')
    _atomic_write = summary._atomic_write
    path=summary.summary_paths('2026-10-23')[0];path.parent.mkdir(parents=True);path.write_bytes(b'old')
    transition=Transition(tmp_path,'dynamic')
    with transition.owner():
        with pytest.raises(RuntimeError):transition.execute([
            lambda:_atomic_write(path,'phase1'),lambda:_atomic_write(path,'phase2')],
            verify=lambda:(_ for _ in ()).throw(RuntimeError('later stage')))
    resumed=Transition(tmp_path,'dynamic')
    with resumed.owner():resumed.execute([lambda:_atomic_write(path,'final')],verify=lambda:None)
    assert path.read_bytes()==b'final'
    path.write_bytes(b'newer-writer')
    with resumed.owner():
        with pytest.raises(ValueError,match='rollback_cas'):resumed.rollback(verify_before=lambda:None)
    assert path.read_bytes()==b'newer-writer'


def test_native_stage_adapter_scopes_environment_and_refuses_trading(monkeypatch):
    import os
    from pathlib import Path
    from src.engine.automation.main_trailing_research_handoff import native_stage_runner
    from src.engine.scalping import pre_submit_delay_tuning as producer
    env={'POSTCLOSE_STAGE_WORKER':'1','POSTCLOSE_SOURCE_DATE':'2026-10-08','BROKER_FAKE_OVERRIDE':'bad'}
    before=os.environ.get('POSTCLOSE_STAGE_WORKER')
    def native(args):
        assert args==['--date','2026-10-08']
        assert os.environ['POSTCLOSE_SOURCE_DATE']=='2026-10-08'
        assert 'BROKER_FAKE_OVERRIDE' not in os.environ
        raise RuntimeError('native failure')
    monkeypatch.setattr(producer,'main',native)
    project=Path(__file__).resolve().parents[2]
    with pytest.raises(RuntimeError,match='native failure'):
        native_stage_runner(['python','-m','src.engine.scalping.pre_submit_delay_tuning','--date','2026-10-08'],env=env,cwd=project)
    assert os.environ.get('POSTCLOSE_STAGE_WORKER')==before
    with pytest.raises(ValueError,match='adapter_invalid'):
        native_stage_runner(['python','-m','src.engine.kiwoom_sniper_v2'],env=env,cwd=project)


def test_native_snapshot_writer_joins_journal_and_rejects_eod(tmp_path,monkeypatch):
    from src.engine import log_archive_service as archive
    path=tmp_path/'data/report/monitor_snapshots/holding_exit_observation_2026-10-08.json'
    monkeypatch.setattr(archive,'MONITOR_SNAPSHOT_DIR',path.parent)
    transition=Transition(tmp_path,'snapshots')
    def fail():raise RuntimeError('later strict failed')
    with transition.owner():
        with pytest.raises(RuntimeError):
            transition.execute([lambda:archive.save_monitor_snapshot('holding_exit_observation','2026-10-08',{'date':'2026-10-08'}),fail],verify=lambda:None)
        transition.rollback(verify_before=lambda:None)
    assert not path.exists()
    transition=Transition(tmp_path,'eod-prohibited')
    with transition.owner(),pytest.raises(ValueError,match='trade_snapshot_regeneration_forbidden'):
        transition.execute([lambda:archive.save_monitor_snapshot('trade_review','2026-10-08',{})],verify=lambda:None)
