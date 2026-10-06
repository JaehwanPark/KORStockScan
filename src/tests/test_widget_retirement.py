"""Permanent retirement boundaries and surviving consumers; no live I/O."""

from dataclasses import replace
from datetime import date, datetime
import json
from pathlib import Path

import pytest

from src.engine.automation import postclose_summary_handoff as handoff
from src.engine.automation import machine_research_closed_loop_refresh as refresh
from src.engine.monitoring import research_closed_loop as loop
from src.trading.order.owner_custody_registry import (
    OrderOwnerRegistry, OwnerOrderContext, OwnerRegistryError,
)


def test_historical_owner_context_cannot_reserve_new_orders(tmp_path, monkeypatch):
    monkeypatch.setenv('KORSTOCKSCAN_BROKER_ACCOUNT_KEY', 'retirement-test-account')
    context = OwnerOrderContext('widget_auto_trade', 'historical', 'historical-position', 'new-intent')
    context.validate()  # Immutable journal identity remains readable.
    registry = OrderOwnerRegistry(tmp_path / 'journal.jsonl')
    assert not registry.path.exists()
    for side in ('BUY', 'SELL'):
        with pytest.raises(OwnerRegistryError, match='permanently_retired'):
            registry.reserve(context=context, symbol='005930', side=side,
                             quantity=10, route='SOR', order_date='2026-10-06')
    assert not registry.path.exists()


def test_old_coexistence_shape_cannot_grant_widget_execution():
    from src.trading.config.symbol_owner_policy import SymbolOwnerDecision, COEXIST_ENTRY_ENABLED
    decision = SymbolOwnerDecision('005930', '2026-10-06', COEXIST_ENTRY_ENABLED,
        ('main_scalping', 'episode', 'widget_auto_trade'), True, True,
        'legacy-policy', 'a'*64, 'historical.json', 'exact_date_policy_resolved')
    assert not decision.owner_allowed('widget_auto_trade')
    assert not decision.owner_allowed('widget_auto_trade', new_entry=False)
    assert decision.owner_allowed('episode')
    assert decision.owner_allowed('main_scalping')


def test_widget_contract_cannot_reenter_postclose_or_admission(tmp_path):
    assert 'widget' not in handoff.INDEPENDENT_SOURCES
    assert 'widget_policy' not in handoff.STAGE_REGISTRY
    assert 'collector_recommendation' not in handoff.STAGE_REGISTRY
    for stage in ('widget_policy', 'collector_recommendation'):
        with pytest.raises(ValueError, match='unknown_postclose_stage'):
            handoff.stage_path(tmp_path, '2026-10-06', stage)
    with pytest.raises(ValueError, match='retired_or_unknown'):
        refresh.read_studies(date(2026, 10, 2), report_root=tmp_path, families=('widget',))
    # Old admission index bytes cannot restore the retired lane.
    folder=tmp_path/'admissions'; folder.mkdir()
    (folder/'symbol_index.json').write_text('{untrusted historical bytes')
    assert loop.admission_symbols(date(2026, 10, 6), owner='widget', directory=tmp_path) == {}
    with pytest.raises(ValueError):
        loop.admission_symbols(date(2026, 10, 6), owner='episode', directory=tmp_path)


def test_native_owner_kernel_does_not_need_widget_package():
    from src.engine.monitoring.machine_entry_confirmation_study import frozen_native_owner_code
    code = frozen_native_owner_code()
    assert code and all('widget' not in name for name in code)
    assert 'src/trading/order/regular_two_leg_machine.py' in code
    from src.web.app import app
    assert all('widget' not in name for name in app.blueprints)
    client=app.test_client()
    for path in ('/api/samsung-price', '/api/doosan-price', '/api/hanwha-ocean-price',
                 '/api/samsung-price-widget/manual-order'):
        assert client.get(path).status_code == 404
        assert client.post(path, json={'side': 'BUY', 'quantity': 10}).status_code == 404


def test_episode_ws_fact_projection_uses_aware_clock_and_existing_worker(tmp_path, monkeypatch):
    from src.engine.kiwoom_websocket import KiwoomWSManager
    from src.engine.monitoring import research_source_facts
    monkeypatch.setattr(loop, 'DIRECTORY', tmp_path)
    calls=[]
    class Writer:
        def __init__(self, symbols):
            assert tuple(symbols) == ()  # No widget watch symbols/subscription request.
        def collect_once(self, now):
            assert now.tzinfo is not None
            calls.append(now)
            return {'remote_requests': 0, 'written_facts': 1}
    monkeypatch.setattr(research_source_facts, 'SharedResearchFactWriter', Writer)
    manager=KiwoomWSManager.__new__(KiwoomWSManager)
    now=datetime.fromisoformat('2026-10-06T09:10:00+09:00')
    assert manager._capture_episode_research_facts(now)['remote_requests'] == 0
    writer=manager._episode_research_fact_writer
    assert manager._capture_episode_research_facts(now)['written_facts'] == 1
    assert manager._episode_research_fact_writer is writer and calls == [now, now]
    with loop.writer_lock(tmp_path/'episode_native_fact_capture', blocking=False):
        with pytest.raises(BlockingIOError):
            manager._capture_episode_research_facts(now)
    assert len(calls) == 2


def test_episode_publication_roundtrip_and_drift_without_widget_study(tmp_path, monkeypatch):
    from src.engine.monitoring import low_price_two_leg_expanded_candidate_research as study
    day=date(2026, 10, 2)
    root=tmp_path/'report'; directory=tmp_path/'runtime'/'machine_research_closed_loop'
    monkeypatch.setattr(refresh, 'DATA_DIR', tmp_path/'data')
    monkeypatch.setenv('POSTCLOSE_POLICY_PUBLICATION_DATE', '2026-10-02')
    monkeypatch.delenv('POSTCLOSE_PREPARED_EFFECTIVE_DATE', raising=False)
    report=dict(schema=study.REPORT_SCHEMA, target_date=str(day), end_date=str(day),
        start_date='2026-06-05', status='no_qualified_candidate', profiles={}, recommendations=[],
        postclose_logic_recommendations=[], recommendation_count=0, trading_date_count=72,
        calibration_trading_day_count=56, holdout_trading_day_count=16,
        closed_loop_contract=loop.SCHEMA, **loop.AUTHORITY)
    with loop.research_scope(directory):
        path=study.write_report(report, root/'low_price_two_leg_expanded_candidate_research')
    result=refresh.refresh(day, directory=directory, report_root=root, publish=True)
    assert result['status'] == 'complete' and result['active_families'] == ['episode']
    assert set(result['publications']) == {'episode'}
    assert refresh.validate_current_receipt(result, day)
    child=result['publications']['episode']
    assert child['profile_count'] == 0  # Removing widget does not allocate extra capital.
    policy_path=Path(child['policy_path'])
    policy_path.write_text('{}')
    assert not refresh.validate_current_receipt(result, day)
    assert not (directory.parent/'widget_symbol_runtime_policy').exists()


def test_rollback_release_cannot_restore_widget_surface(tmp_path):
    from src.engine.infrastructure.runtime_release_router import _validate_retired_surfaces
    root=tmp_path / "release"
    path=tmp_path / "data/runtime/retirements/widget-retirement-2026-10-06.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(dict(schema="widget_retirement_transition_v1", state="terminal", owner="widget_auto_trade")))
    _validate_retired_surfaces(tmp_path, root)
    old=root / "deploy/run_widget_evaluation.sh"
    old.parent.mkdir(parents=True);old.write_text("retired")
    with pytest.raises(ValueError, match="restores_permanently_retired"):
        _validate_retired_surfaces(tmp_path, root)


@pytest.mark.parametrize("day,schema,accepted", [
    ("2026-10-02", "postclose_stage_terminal_v2", True),
    ("2026-10-06", "postclose_stage_terminal_v2", False),
    ("2026-10-06", "postclose_stage_terminal_v3", True),
])
def test_retirement_generation_rejects_old_stage_receipt(tmp_path, day, schema, accepted):
    import hashlib
    from src.engine.error_detectors.artifact_freshness import _semantic_stage_binding
    path=tmp_path / "data/report/postclose_stage_terminal" / day / "legacy_machine_report.json"
    path.parent.mkdir(parents=True)
    body=dict(schema=schema, source_date=day, stage_id="legacy_machine_report", status="succeeded", exit_code=0)
    sha=hashlib.sha256(json.dumps(body,ensure_ascii=True,sort_keys=True,separators=(",", ":")).encode()).hexdigest()
    path.write_text(json.dumps(dict(body,receipt_sha256=sha)))
    if accepted:
        assert _semantic_stage_binding(tmp_path, day, "legacy_machine_report")["status"] == "succeeded"
    else:
        with pytest.raises(ValueError, match="identity_or_hash_invalid"):
            _semantic_stage_binding(tmp_path, day, "legacy_machine_report")


def test_episode_publication_rejects_missing_execution_source_before_writes(tmp_path):
    report=dict(profiles={"episode-native":dict(execution_feasibility=dict(source_generations={str(tmp_path/"missing.jsonl"):[1,2,3]}))})
    with pytest.raises((OSError, ValueError)):
        refresh._study_source_generations(report)
    assert not (tmp_path/"research_publication_2026-10-07.json").exists()
