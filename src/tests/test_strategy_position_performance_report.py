from contextlib import contextmanager
import copy
import gzip
import json

import pytest

from src.engine import strategy_position_performance_report as report_mod


def test_main_synchronizes_target_date_without_building_provider_or_runtime_work(
    monkeypatch,
):
    calls = []
    monkeypatch.setattr(
        report_mod,
        "sync_trade_performance_for_date",
        lambda target_date: calls.append(target_date)
        or {"target_date": target_date, "fact_count": 8},
    )

    assert report_mod.main(["--date", "2026-08-25"]) == 0
    assert calls == ["2026-08-25"]


def _native_fact_projection(tmp_path, monkeypatch, *, count=2, large=True, scope='entered'):
    from src.engine import log_archive_service as archive
    from src.engine.sniper_trade_review_report import completed_census_manifest, strategy_fact_projection_rows
    from src.engine.lifecycle.broker_cost_reconciliation import source_generation
    day = '2026-10-08'
    monkeypatch.setattr(archive, 'MONITOR_SNAPSHOT_DIR', tmp_path/'report/monitor_snapshots')
    monkeypatch.setattr(report_mod, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(report_mod, '_FACT_SYNC_STATUS_DIR', tmp_path/'report/fact_sync')
    monkeypatch.setattr(report_mod, '_enrich_scanner_provenance', lambda facts, *a, **k: facts)
    rows = [dict(id=i+1, rec_date=day, code='005930', name='native', status='HOLDING',
        strategy='SCALPING', position_tag='SCANNER', buy_price=1000, buy_qty=1,
        buy_time=day+' 09:00:00', sell_time=None, sell_price=None, profit_rate=None,
        add_count=0, avg_down_count=0, pyramid_count=0,
        timeline='x'*(5*1024*1024) if large and i == 0 else []) for i in range(count)]
    if rows:
        rows[0].update(status='COMPLETED', sell_price=1010, sell_time=day+' 09:10:00')
    completed = [{**rows[0], 'completion_observed_date': day, 'terminal_population_scope': 'real_record_bound',
        'strict_completion_status': 'excluded', 'broker_actual_cost_observed': False,
        'actual_cost_reconciliation': {'status': 'actual_cost_unallocated'}, 'realized_pnl_krw': None,
        'realized_pnl_krw_source': 'missing_exact_cost', 'broker_actual_fees_taxes_krw': None}] if rows else []
    payload = dict(date=day, code=None, since=None, scope=scope,
        meta=dict(snapshot_profile='postclose_exit', warnings=[], sell_completed_event_ids=[1] if rows else [],
                  actual_cost_source_generation=source_generation(tmp_path,day)),
        metrics=dict(total_trades=len(rows), canonical_completed_trades=len(completed)),
        sections=dict(recent_trades=rows[:300], strategy_position_fact_projection=strategy_fact_projection_rows(rows),
                      completed_trade_projection=completed, open_scalp_position_projection=[]))
    payload['meta']['completed_census_manifest'] = completed_census_manifest(payload)
    return day, archive.save_monitor_snapshot('trade_review', day, payload)


@pytest.mark.parametrize('count', [0, 2, 303])
def test_native_fact_projection_preserves_full_census_without_timelines(tmp_path, monkeypatch, count):
    day, path = _native_fact_projection(tmp_path, monkeypatch, count=count)
    monkeypatch.setattr(report_mod, 'build_trade_review_report', lambda **k: pytest.fail('rebuilt original report'))
    monkeypatch.setattr(report_mod, 'load_monitor_snapshot', lambda *a: pytest.fail('decoded original snapshot'))
    native = report_mod._load_completion_fact_projection(day, path)
    assert len(native['sections']['recent_trades']) == count
    assert all('timeline' not in row for row in native['sections']['recent_trades'])
    assert path.with_suffix('.fact_projection.json').stat().st_size < 512*1024
    quality = {}
    facts, warnings = report_mod._build_trade_fact_rows(day, completion_snapshot=path, completion_census_quality=quality)
    assert len(facts) == count and warnings == []
    if count:
        assert (facts[0]['profit_rate'], facts[0]['realized_pnl_krw']) == (None, None)
        assert facts[0]['actual_cost_reconciliation_status'] == 'actual_cost_unallocated'
    assert quality['completion_snapshot_source'] == native['_native_source_proof']
    report_mod._write_status(day, dict(status='succeeded' if count else 'valid_empty',
        completed_census_run_ids=[quality['run_id']], completed_census_projection_sha256=[quality['projection_sha256']],
        actual_cost_source_generation=quality['actual_cost_source_generation'],
        completion_snapshot_source=quality['completion_snapshot_source']))
    assert report_mod._saved_fact_generation_issue(day) is None


@pytest.mark.parametrize('mutation', ['missing', 'bytes', 'cost', 'identity', 'wrong_date', 'wrong_path', 'symlink', 'generation'])
def test_native_fact_projection_rejects_missing_stale_or_unbound_source(tmp_path, monkeypatch, mutation):
    from src.engine.lifecycle.broker_cost_reconciliation import receipt_path
    day, path = _native_fact_projection(tmp_path, monkeypatch)
    target = path.with_suffix('.fact_projection.json')
    if mutation == 'missing':
        target.unlink()
    elif mutation in {'bytes', 'generation'}:
        raw = target.read_bytes()
        if mutation == 'generation':
            value = json.loads(raw)
            value['sections']['recent_trades'][0]['buy_qty'] = 2
            value['artifact_sha256'] = report_mod._canonical_sha256({k:v for k,v in value.items() if k!='artifact_sha256'})
            raw = json.dumps(value).encode()
        target.write_bytes(raw + b' ')
    elif mutation == 'cost':
        cost = receipt_path(tmp_path, day, '1')
        cost.parent.mkdir(parents=True)
        cost.write_text('{"corrected":1}')
    elif mutation == 'identity':
        with path.open('ab') as handle:
            handle.write(b' ')
    elif mutation == 'wrong_date':
        day = '2026-10-07'
    elif mutation == 'wrong_path':
        path = tmp_path/'other.json'
    elif mutation == 'symlink':
        other = path.with_suffix('.saved')
        path.rename(other)
        path.symlink_to(other)
    with pytest.raises(report_mod.FactSyncSourceError):
        report_mod._load_completion_fact_projection(day, path)


def test_native_fact_projection_source_survives_lossless_archive(tmp_path, monkeypatch):
    from src.engine import compress_db_backfilled_files as archive
    day, path = _native_fact_projection(tmp_path, monkeypatch)
    before = report_mod._load_completion_fact_projection(day, path)['_native_source_proof']
    monkeypatch.setattr(archive, 'MONITOR_SNAPSHOT_DIR', path.parent)
    for source in (path, path.with_suffix('.completed_projection.json'), path.with_suffix('.fact_projection.json')):
        assert archive._gzip_file(source, dry_run=False)[0]
    after = report_mod._load_completion_fact_projection(day, path)['_native_source_proof']
    assert before == after


def test_native_fact_projection_rejects_unentered_display_scope(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match='fact_projection_census_invalid'):
        _native_fact_projection(tmp_path, monkeypatch, scope='all')


def _original_native_fact_source(path):
    """Keep the fixture's original raw/projection bytes, with the old v1 seal."""
    from src.engine.lifecycle import holding_window_generation as window
    sidecar = path.with_suffix('.completed_projection.json')
    completed = json.loads(sidecar.read_bytes())
    path.with_suffix('.fact_projection.json').unlink()
    window.seal_dependency_receipt(sidecar, completed)


def test_original_native_stream_restores_binding_without_rewriting_historical_sources(tmp_path, monkeypatch):
    from src.engine.scalping import initial_quantity_policy as quantity
    from src.engine import log_archive_service as archive
    import hashlib
    day, path = _native_fact_projection(tmp_path, monkeypatch)
    _original_native_fact_source(path)
    files = [path, path.with_suffix('.completed_projection.json'),
             path.with_suffix('.completed_projection.json.dependencies.json')]
    original = {str(file): hashlib.sha256(file.read_bytes()).hexdigest() for file in files}
    quality = {}
    facts, warnings = report_mod._build_trade_fact_rows(day, completion_snapshot=path, completion_census_quality=quality)
    assert len(facts) == 2 and warnings == []
    proof = quality['completion_snapshot_source']
    assert proof['source_basis'] == 'native_original_snapshot_stream' and proof['fact_projection'] is None
    assert facts[0]['completion_census_run_id'] == quality['run_id']
    assert facts[0]['completion_census_projection_sha256'] == quality['projection_sha256']
    assert (facts[0]['profit_rate'], facts[0]['realized_pnl_krw']) == (None, None)
    report_mod._write_status(day, dict(status='succeeded', completed_census_run_ids=[quality['run_id']],
        completed_census_projection_sha256=[quality['projection_sha256']],
        actual_cost_source_generation=quality['actual_cost_source_generation'], completion_snapshot_source=proof))
    monkeypatch.setattr(quantity, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(archive, 'MONITOR_SNAPSHOT_DIR', path.parent)
    monkeypatch.setattr(report_mod, '_stream_original_fact_projection', lambda *a: pytest.fail('historical source rescanned'))
    monkeypatch.setattr(report_mod, 'load_monitor_snapshot', lambda *a: pytest.fail('historical source decoded'))
    assert report_mod._saved_fact_generation_issue(day) is None
    assert quantity._quantity_fact_generation_issue(day) is None
    assert {str(file): hashlib.sha256(file.read_bytes()).hexdigest() for file in files} == original
    assert not path.with_suffix('.fact_projection.json').exists()


def test_original_native_stream_rejects_display_truncation(tmp_path, monkeypatch):
    day, path = _native_fact_projection(tmp_path, monkeypatch, count=303)
    _original_native_fact_source(path)
    with pytest.raises(report_mod.FactSyncSourceError, match='legacy_display_census_unverified'):
        report_mod._load_completion_fact_projection(day, path)


def test_native_fact_sync_cli_passes_explicit_source_only_when_requested(monkeypatch):
    calls = []
    monkeypatch.setattr(report_mod, 'sync_trade_performance_for_date', lambda day, **kw: calls.append((day,kw)) or {})
    path = '/native/trade_review_2026-10-08.json'
    assert report_mod.main(['--date', '2026-10-08', '--completion-snapshot', path]) == 0
    from pathlib import Path
    assert calls == [('2026-10-08', {'completion_snapshot': Path(path)})]


@pytest.mark.parametrize('failure', [None, 'missing', 'changed_before_write', 'changed_during_aggregate', 'changed_during_write'])
def test_native_fact_sync_preserves_database_on_invalid_source_and_null_costs(tmp_path, monkeypatch, failure):
    from datetime import date
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from src.database.models import TradePerformanceFact, StrategyPositionPerformanceDaily
    from src.engine.scalping import scale_in_split_order_plan
    day, path = _native_fact_projection(tmp_path, monkeypatch)
    engine = create_engine('sqlite:///:memory:')
    TradePerformanceFact.__table__.create(engine)
    StrategyPositionPerformanceDaily.__table__.create(engine)
    class DB:
        def init_db(self): pass
        def analyze_performance_tables(self): pass
        @contextmanager
        def get_session(self):
            with Session(engine) as session, session.begin():
                yield session
    monkeypatch.setattr(report_mod, '_DB', DB())
    monkeypatch.setattr(scale_in_split_order_plan, '_query_actual_fill_inventory', lambda _: [])
    with Session(engine) as session, session.begin():
        session.add(TradePerformanceFact(recommendation_id=99, rec_date=date.fromisoformat(day),
            stock_code='005930', strategy='SCALPING', position_tag='SCANNER', status='HOLDING'))
    if failure == 'missing':
        path.with_suffix('.fact_projection.json').unlink()
    elif failure == 'changed_before_write':
        original = report_mod._validate_fact_batch
        def changed(*args, **kwargs):
            with path.with_suffix('.fact_projection.json').open('ab') as handle:
                handle.write(b' ')
            return original(*args, **kwargs)
        monkeypatch.setattr(report_mod, '_validate_fact_batch', changed)
    elif failure == 'changed_during_aggregate':
        original = report_mod._aggregate_daily_rows
        def changed(*args, **kwargs):
            with path.with_suffix('.fact_projection.json').open('ab') as handle:
                handle.write(b' ')
            return original(*args, **kwargs)
        monkeypatch.setattr(report_mod, '_aggregate_daily_rows', changed)
    elif failure == 'changed_during_write':
        original = Session.bulk_insert_mappings
        def changed(session, *args, **kwargs):
            value = original(session, *args, **kwargs)
            with path.with_suffix('.fact_projection.json').open('ab') as handle:
                handle.write(b' ')
            return value
        monkeypatch.setattr(Session, 'bulk_insert_mappings', changed)
    if failure:
        with pytest.raises(report_mod.FactSyncSourceError, match='source_blocked'):
            report_mod.sync_trade_performance_for_date(day, completion_snapshot=path)
        with Session(engine) as session:
            assert [row.recommendation_id for row in session.query(TradePerformanceFact)] == [99]
        assert json.loads(report_mod._status_path(day).read_bytes())['status'] == 'source_blocked'
    else:
        result = report_mod.sync_trade_performance_for_date(day, completion_snapshot=path)
        assert result['status'] == 'succeeded' and result['fact_count'] == 2
        with Session(engine) as session:
            assert session.get(TradePerformanceFact, 99) is None
            completed = session.get(TradePerformanceFact, 1)
            assert (completed.profit_rate, completed.realized_pnl_krw) == (None, None)
        assert report_mod._saved_fact_generation_issue(day) is None


def test_build_trade_fact_rows_normalizes_strategy_and_exit_fields(monkeypatch):
    monkeypatch.setattr(
        report_mod,
        "build_trade_review_report",
        lambda target_date, since_time=None, top_n=100000, scope="entered": {
            "meta": {"warnings": []},
            "sections": {
                "recent_trades": [
                    {
                        "id": 101,
                        "rec_date": target_date,
                        "code": "111111",
                        "name": "테스트A",
                        "status": "COMPLETED",
                        "strategy": "scalp",
                        "position_tag": None,
                        "buy_price": 1000,
                        "buy_qty": 2,
                        "buy_time": "2026-04-06 09:00:00",
                        "sell_price": 1030,
                        "sell_time": "2026-04-06 09:03:00",
                        "profit_rate": 3.0,
                        "realized_pnl_krw": 60,
                        "holding_seconds": 180,
                        "exit_signal": {
                            "exit_rule": "scalp_trailing_take_profit",
                            "sell_reason_type": "TRAILING",
                        },
                        "ai_review_summary": {"headline": "AI 보유 유지 우세"},
                        "gatekeeper_replay": {
                            "action": "즉시 매수",
                            "allow_entry": True,
                        },
                    }
                ]
            },
        },
    )

    facts, warnings = report_mod._build_trade_fact_rows("2026-04-06")

    assert warnings == []
    assert len(facts) == 1
    fact = facts[0]
    assert fact["strategy"] == "SCALPING"
    assert fact["position_tag"] == "SCALP_BASE"
    assert fact["exit_rule"] == "scalp_trailing_take_profit"
    assert fact["sell_reason_type"] == "TRAILING"
    assert fact["ai_review_headline"] == "AI 보유 유지 우세"
    assert fact["gatekeeper_action"] == "즉시 매수"
    assert fact["gatekeeper_allow_entry"] is True


def test_strategy_position_report_falls_back_without_db(monkeypatch):
    monkeypatch.setattr(
        report_mod,
        "build_trade_review_report",
        lambda target_date, since_time=None, top_n=100000, scope="entered": {
            "meta": {"warnings": []},
            "sections": {
                "recent_trades": [
                    {
                        "id": 1,
                        "rec_date": target_date,
                        "code": "111111",
                        "name": "테스트A",
                        "status": "COMPLETED",
                        "strategy": "SCALPING",
                        "position_tag": "SCANNER",
                        "buy_price": 1000,
                        "buy_qty": 1,
                        "buy_time": "2026-04-06 09:00:00",
                        "sell_price": 1050,
                        "sell_time": "2026-04-06 09:02:00",
                        "profit_rate": 5.0,
                        "realized_pnl_krw": 50,
                        "holding_seconds": 120,
                        "exit_signal": {
                            "exit_rule": "take_profit",
                            "sell_reason_type": "PROFIT",
                        },
                    },
                    {
                        "id": 2,
                        "rec_date": target_date,
                        "code": "222222",
                        "name": "테스트B",
                        "status": "COMPLETED",
                        "strategy": "SCALPING",
                        "position_tag": "VCP_NEXT",
                        "buy_price": 2000,
                        "buy_qty": 1,
                        "buy_time": "2026-04-06 09:10:00",
                        "sell_price": 1900,
                        "sell_time": "2026-04-06 09:20:00",
                        "profit_rate": -5.0,
                        "realized_pnl_krw": -100,
                        "holding_seconds": 600,
                        "exit_signal": {
                            "exit_rule": "stop_loss",
                            "sell_reason_type": "LOSS",
                        },
                    },
                    {
                        "id": 4,
                        "rec_date": target_date,
                        "code": "444444",
                        "name": "테스트D",
                        "status": "COMPLETED",
                        "strategy": "SCALPING",
                        "position_tag": "SCANNER",
                        "buy_price": 10000,
                        "buy_qty": 1,
                        "buy_time": "2026-04-06 09:30:00",
                        "sell_price": 11000,
                        "sell_time": "2026-04-06 09:40:00",
                        "profit_rate": 1.0,
                        "realized_pnl_krw": 1000,
                        "holding_seconds": 600,
                        "exit_signal": {
                            "exit_rule": "take_profit",
                            "sell_reason_type": "PROFIT",
                        },
                    },
                    {
                        "id": 5,
                        "rec_date": target_date,
                        "code": "555555",
                        "name": "테스트E",
                        "status": "COMPLETED",
                        "strategy": "SCALPING",
                        "position_tag": "SCANNER",
                        "buy_price": 10000,
                        "buy_qty": 1,
                        "buy_time": "2026-04-06 09:45:00",
                        "sell_price": 9800,
                        "sell_time": "2026-04-06 09:55:00",
                        "profit_rate": -2.0,
                        "realized_pnl_krw": -200,
                        "holding_seconds": 600,
                        "exit_signal": {
                            "exit_rule": "stop_loss",
                            "sell_reason_type": "LOSS",
                        },
                    },
                    {
                        "id": 3,
                        "rec_date": target_date,
                        "code": "333333",
                        "name": "테스트C",
                        "status": "HOLDING",
                        "strategy": "KOSPI_ML",
                        "position_tag": "MIDDLE",
                        "buy_price": 3000,
                        "buy_qty": 1,
                        "buy_time": "2026-04-06 10:00:00",
                        "sell_price": 0,
                        "sell_time": "",
                        "profit_rate": 0.0,
                        "realized_pnl_krw": 0,
                        "holding_seconds": None,
                        "exit_signal": None,
                    },
                ]
            },
        },
    )

    @contextmanager
    def _broken_session():
        raise RuntimeError("db unavailable")
        yield None

    monkeypatch.setattr(report_mod._DB, "get_session", _broken_session)

    report = report_mod.build_strategy_position_performance_report("2026-04-06")

    assert report["summary"]["strategy_count"] == 2
    assert report["summary"]["tag_group_count"] == 3
    assert report["summary"]["entered_count"] == 5
    assert report["summary"]["completed_count"] == 4
    assert report["summary"]["open_count"] == 1
    assert report["summary"]["realized_pnl_krw"] == 696
    assert len(report["kpis"]) == 8
    kpi_map = {item["label"]: item for item in report["kpis"]}
    assert kpi_map["종료 승률"]["value"] == "50.0%"
    assert kpi_map["평균 기대손익"]["value"] == "174원"
    assert kpi_map["미종료 비중"]["value"] == "20.0%"
    assert kpi_map["최고 성과 버킷"]["value"] == "SCALPING/SCANNER"
    assert kpi_map["주의 버킷"]["value"] == "SCALPING/VCP_NEXT"
    assert kpi_map["최고 익절 거래"]["value"] == "테스트D(444444)"
    assert kpi_map["최대 손실 거래"]["value"] == "테스트E(555555)"
    assert kpi_map["최고 익절 거래"]["detail"] == "+9.75% / 975원"
    assert kpi_map["최대 손실 거래"]["detail"] == "-2.23% / -223원"

    row_map = {(row["strategy"], row["position_tag"]): row for row in report["rows"]}
    assert row_map[("SCALPING", "SCANNER")]["realized_pnl_krw"] == 800
    assert row_map[("SCALPING", "VCP_NEXT")]["realized_pnl_krw"] == -104
    assert row_map[("KOSPI_ML", "KOSPI_BASE")]["open_count"] == 1

    assert report["sections"]["top_winners"][0]["stock_code"] == "111111"
    assert report["sections"]["top_losers"][0]["stock_code"] == "222222"


def test_scanner_discovery_type_performance_section(monkeypatch):
    monkeypatch.setattr(
        report_mod,
        "build_trade_review_report",
        lambda target_date, since_time=None, top_n=100000, scope="entered": {
            "meta": {"warnings": []},
            "sections": {
                "recent_trades": [
                    {
                        "id": 11,
                        "rec_date": target_date,
                        "code": "111111",
                        "name": "가격급등",
                        "status": "COMPLETED",
                        "strategy": "SCALPING",
                        "position_tag": "SCANNER",
                        "buy_price": 1000,
                        "buy_qty": 1,
                        "buy_time": "2026-04-06 09:10:00",
                        "sell_price": 1020,
                        "sell_time": "2026-04-06 09:20:00",
                        "profit_rate": 2.0,
                        "realized_pnl_krw": 20,
                        "holding_seconds": 600,
                        "exit_signal": {
                            "exit_rule": "take_profit",
                            "sell_reason_type": "PROFIT",
                        },
                    },
                    {
                        "id": 12,
                        "rec_date": target_date,
                        "code": "222222",
                        "name": "저점반등",
                        "status": "COMPLETED",
                        "strategy": "SCALPING",
                        "position_tag": "SCANNER",
                        "buy_price": 1000,
                        "buy_qty": 1,
                        "buy_time": "2026-04-06 10:10:00",
                        "sell_price": 990,
                        "sell_time": "2026-04-06 10:20:00",
                        "profit_rate": -1.0,
                        "realized_pnl_krw": -10,
                        "holding_seconds": 600,
                        "exit_signal": {
                            "exit_rule": "stop_loss",
                            "sell_reason_type": "LOSS",
                        },
                    },
                ]
            },
        },
    )
    monkeypatch.setattr(
        report_mod,
        "_load_scanner_promotion_events",
        lambda target_date: {
            "111111": [
                {
                    "emitted_at": report_mod._parse_datetime("2026-04-06T09:00:00"),
                    "scanner_discovery_type": "price_jump_acceleration",
                    "scanner_promotion_reason": "price_jump_start_acceleration",
                    "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
                    "scanner_source_role": "early_discovery",
                    "scanner_priority_tier": "tier_a_acceleration_confirmed",
                }
            ],
            "222222": [
                {
                    "emitted_at": report_mod._parse_datetime("2026-04-06T10:00:00"),
                    "scanner_discovery_type": "low_rebound_rising_missed",
                    "scanner_promotion_reason": "low_rebound_rising_missed_candidate",
                    "source_signature": "LOW_REBOUND_RISING_MISSED",
                    "scanner_source_role": "rising_missed_low_rebound_candidate",
                    "scanner_priority_tier": "tier_c_volume_confirmation",
                    "rising_missed_lineage": "low_rebound_from_intraday_low",
                }
            ],
        },
    )

    facts, _warnings = report_mod._build_trade_fact_rows("2026-04-06")
    summary_rows = report_mod._aggregate_daily_rows(facts)
    report = report_mod._build_report_payload(
        "2026-04-06",
        [
            {
                **fact,
                "buy_time": (
                    fact["buy_time"].strftime("%Y-%m-%d %H:%M:%S")
                    if fact["buy_time"]
                    else ""
                ),
                "sell_time": (
                    fact["sell_time"].strftime("%Y-%m-%d %H:%M:%S")
                    if fact["sell_time"]
                    else ""
                ),
            }
            for fact in facts
        ],
        [{**row, "rec_date": row["rec_date"].isoformat()} for row in summary_rows],
    )

    scanner_rows = {
        row["scanner_discovery_type"]: row
        for row in report["sections"]["scanner_discovery_rows"]
    }
    assert report["summary"]["scanner_discovery_type_count"] == 2
    assert report["summary"]["scanner_provenance_matched_count"] == 2
    assert scanner_rows["price_jump_acceleration"]["realized_pnl_krw"] == 18
    assert (
        scanner_rows["price_jump_acceleration"]["top_promotion_reason"]
        == "price_jump_start_acceleration"
    )
    assert scanner_rows["low_rebound_rising_missed"]["realized_pnl_krw"] == -12
    assert scanner_rows["low_rebound_rising_missed"]["provenance_missing_count"] == 0


def test_completed_row_with_missing_execution_economics_stays_null(monkeypatch):
    monkeypatch.setattr(
        report_mod,
        "build_trade_review_report",
        lambda **_kwargs: {
            "meta": {"warnings": []},
            "sections": {
                "recent_trades": [
                    {
                        "id": 1,
                        "rec_date": "2026-04-06",
                        "code": "111111",
                        "status": "COMPLETED",
                        "strategy": "SCALPING",
                        "position_tag": "SCANNER",
                        "buy_price": 1000,
                        "buy_qty": 1,
                        "buy_time": "2026-04-06 09:00:00",
                        "sell_price": None,
                        "sell_time": None,
                    }
                ]
            },
        },
    )

    facts, warnings = report_mod._build_trade_fact_rows("2026-04-06")
    rows = report_mod._aggregate_daily_rows(facts)

    assert warnings == []
    assert facts[0]["profit_rate"] is None
    assert facts[0]["realized_pnl_krw"] is None
    assert rows[0]["economics_valid_completed_count"] == 0
    assert rows[0]["economics_missing_completed_count"] == 1
    assert rows[0]["realized_pnl_krw"] is None


def test_main_completed_fact_requires_same_generation_and_actual_broker_cost(monkeypatch):
    from src.engine.sniper_trade_review_report import completed_census_manifest

    day = "2026-09-28"
    row = {
        "id": 1, "rec_date": day, "code": "111111", "status": "COMPLETED",
        "strategy": "SCALPING", "position_tag": "SCALP_BASE",
        "buy_price": 1000, "buy_qty": 1, "buy_time": f"{day} 09:00:00",
        "sell_price": 1100, "sell_time": f"{day} 09:10:00",
    }
    projected = {
        **row, "completion_observed_date": day,
        "terminal_population_scope": "real_record_bound",
        "strict_completion_status": "excluded",
        "strict_completion_reasons": ["source_gap_broker_actual_cost_missing"],
        "configured_fee_estimate_krw": 10,
        "broker_actual_fees_taxes_krw": None,
        "broker_actual_cost_observed": False,
        "realized_pnl_krw": None,
    }
    report = {
        "date": day, "code": None, "since": None,
        "meta": {"warnings": [], "sell_completed_event_ids": [1],
                 "trailing_event_source_receipts": []},
        "metrics": {"canonical_completed_trades": 1},
        "sections": {"recent_trades": [row],
                     "completed_trade_projection": [projected]},
    }
    report["meta"]["completed_census_manifest"] = completed_census_manifest(report)
    monkeypatch.setattr(report_mod, "build_trade_review_report", lambda **_kwargs: report)

    facts, warnings = report_mod._build_trade_fact_rows(day)
    assert warnings == []
    assert facts[0]["profit_rate"] is None
    assert facts[0]["realized_pnl_krw"] is None
    assert facts[0]["economics_source_status"] == "source_gap_broker_actual_cost_missing"

    report["sections"]["recent_trades"][0]["sell_price"] = 1200
    mismatched, _ = report_mod._build_trade_fact_rows(day)
    assert mismatched[0]["economics_source_status"] == (
        "source_gap_completion_projection_identity"
    )
    assert mismatched[0]["realized_pnl_krw"] is None
    report["sections"]["recent_trades"][0]["sell_price"] = 1100

    report["meta"]["warnings"] = ["DB completion source missing"]
    with pytest.raises(report_mod.FactSyncSourceError, match="trade_review_source_warning"):
        report_mod._build_trade_fact_rows(day)
    report["meta"]["warnings"] = []

    report["sections"]["completed_trade_projection"][0]["configured_fee_estimate_krw"] = 99
    with pytest.raises(report_mod.FactSyncSourceError, match="completed_census_generation_mismatch"):
        report_mod._build_trade_fact_rows(day)


def test_saved_fact_generation_rejects_rewritten_trade_review(monkeypatch, tmp_path):
    from src.engine.sniper_trade_review_report import completed_census_manifest

    day = "2026-09-28"
    monkeypatch.setattr(report_mod, "_FACT_SYNC_STATUS_DIR", tmp_path)
    snapshot = {
        "date": day, "code": None, "since": None,
        "meta": {"warnings": [], "sell_completed_event_ids": [],
                 "trailing_event_source_receipts": []},
        "metrics": {"canonical_completed_trades": 0},
        "sections": {"completed_trade_projection": []},
    }
    snapshot["meta"]["completed_census_manifest"] = completed_census_manifest(snapshot)
    monkeypatch.setattr(report_mod, "load_monitor_snapshot", lambda *_args: snapshot)
    report_mod._write_status(day, {
        "status": "valid_empty", "completed_census_run_ids": [
            snapshot["meta"]["completed_census_manifest"]["run_id"]
        ], "completed_census_projection_sha256": [
            snapshot["meta"]["completed_census_manifest"]["projection_sha256"]
        ],
    })
    assert report_mod._saved_fact_generation_issue(day, snapshot=snapshot) is None

    snapshot["meta"]["trailing_event_source_receipts"] = [{"logical_sha256": "new"}]
    snapshot["meta"]["completed_census_manifest"] = completed_census_manifest(snapshot)
    assert report_mod._saved_fact_generation_issue(day, snapshot=snapshot) == "stale_fact_source_generation"


def test_scanner_provenance_never_uses_future_promotion_event():
    fact = {
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "stock_code": "111111",
        "buy_time": report_mod._parse_datetime("2026-04-06 09:00:00"),
    }
    future_event = {
        "emitted_at": report_mod._parse_datetime("2026-04-06 09:01:00"),
        "scanner_discovery_type": "price_jump_acceleration",
    }

    assert (
        report_mod._select_scanner_event_for_trade(fact, {"111111": [future_event]})
        is None
    )


def test_source_warning_preserves_prior_generation_and_writes_blocked_receipt(
    monkeypatch, tmp_path
):
    executed = []
    from src.engine.scalping import scale_in_split_order_plan
    monkeypatch.setattr(scale_in_split_order_plan, "_query_actual_fill_inventory", lambda _: [])

    class _Query:
        def filter(self, *_args):
            return self

        def count(self):
            return 7

    class _Session:
        def query(self, *_args):
            return _Query()

        def execute(self, statement):
            executed.append(statement)

    @contextmanager
    def _session():
        yield _Session()

    monkeypatch.setattr(
        report_mod,
        "_build_trade_fact_rows",
        lambda _target_date, **_kwargs: ([], ["DB connection failed"]),
    )
    monkeypatch.setattr(report_mod._DB, "init_db", lambda: None)
    monkeypatch.setattr(report_mod._DB, "get_session", _session)
    monkeypatch.setattr(report_mod, "_FACT_SYNC_STATUS_DIR", tmp_path)

    with pytest.raises(report_mod.FactSyncSourceError):
        report_mod.sync_trade_performance_for_date("2026-04-06")

    assert executed == []
    receipt = json.loads(
        (tmp_path / "strategy_position_fact_sync_2026-04-06.status.json").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["status"] == "source_blocked"
    assert receipt["prior_fact_count"] == 7
    assert receipt["consumer_ready"] is False


def test_fact_sync_receipt_has_a_verifiable_generation_hash(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "_FACT_SYNC_STATUS_DIR", tmp_path)

    receipt = report_mod._write_status(
        "2026-04-06",
        {
            "status": "succeeded",
            "consumer_ready": True,
            "source_fact_count": 1,
            "fact_count": 1,
        },
    )
    persisted = json.loads(
        (tmp_path / "strategy_position_fact_sync_2026-04-06.status.json").read_text(
            encoding="utf-8"
        )
    )
    actual_hash = persisted.pop("artifact_sha256")

    assert actual_hash == receipt["artifact_sha256"]
    assert actual_hash == report_mod._canonical_sha256(persisted)


def test_existing_scanner_scan_projects_only_filled_ids_and_exact_date(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "_PIPELINE_EVENTS_DIR", tmp_path)
    day = "2026-09-17"
    rows = [{"stage": "scale_in_order_submitted", "emitted_at": stamp, "stock_code": "000001",
             "strategy": "SCALPING", "fields": {"record_id": record, "add_type": "AVG_DOWN", "order_no": "BUY1", "request_qty": 4}}
            for record, stamp in [("1", f"{day}T10:00:00+09:00"), ("2", f"{day}T10:00:00+09:00"), ("1", "2026-09-16T10:00:00+09:00")]]
    (tmp_path / f"pipeline_events_{day}.jsonl").write_text("\n".join(map(json.dumps, rows)))
    projection = {"record_ids": {"1"}, "rows": []}
    report_mod._load_scanner_promotion_events(day, scale_in_projection=projection)
    assert len(projection["rows"]) == 1
    assert projection["rows"][0]["record_id"] == "1"


def test_scanner_promotion_reader_replays_gzip_only_source_into_fact(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "_PIPELINE_EVENTS_DIR", tmp_path)
    day = "2026-09-23"
    event = {"stage": "scalping_scanner_candidate_promoted",
             "emitted_at": f"{day}T09:00:00+09:00", "stock_code": "005930",
             "fields": {"scanner_promotion_id": "PROMO-1",
                        "scanner_promotion_reason": "price_jump_start_acceleration"}}
    logical = tmp_path / f"pipeline_events_{day}.jsonl"
    with gzip.open(f"{logical}.gz", "wt", encoding="utf-8") as handle:
        handle.write(json.dumps(event) + "\n")
    events = report_mod._load_scanner_promotion_events(day)
    assert [row["scanner_promotion_id"] for row in events["005930"]] == ["PROMO-1"]
    fact = {"strategy": "SCALPING", "position_tag": "SCANNER",
            "stock_code": "005930", "buy_time": f"{day} 09:05:00"}
    assert report_mod._enrich_scanner_provenance([fact], day)[0]["scanner_provenance_status"] == "matched"


@pytest.mark.parametrize("representation", ["plain", "gzip", "both"])
def test_scanner_source_representations_have_one_logical_generation(
    monkeypatch, tmp_path, representation,
):
    monkeypatch.setattr(report_mod, "_PIPELINE_EVENTS_DIR", tmp_path)
    day = "2026-09-23"
    event = {"stage": "scalping_scanner_candidate_promoted",
             "emitted_at": f"{day}T09:00:00+09:00", "emitted_date": day,
             "storage_partition_date": day, "stock_code": "005930",
             "fields": {"scanner_promotion_id": "PROMO-1", "venue": "KRX",
                        "market_session_bucket": "KRX_REGULAR"}}
    logical = tmp_path / f"pipeline_events_{day}.jsonl"
    raw = (json.dumps(event) + "\n").encode()
    if representation in {"plain", "both"}:
        logical.write_bytes(raw)
    if representation in {"gzip", "both"}:
        with gzip.open(f"{logical}.gz", "wb") as handle:
            handle.write(raw)
        (tmp_path / f"{logical.name}.gz.archive_receipt.json").write_text(json.dumps({
            "schema": "pipeline_raw_archive_identity_v1",
            "logical_path": str(logical),
            "logical_content_sha256": report_mod.hashlib.sha256(raw).hexdigest(),
            "archive_generation": {"size_bytes": (tmp_path / f"{logical.name}.gz").stat().st_size},
        }))
    quality = {}
    rows = report_mod._load_scanner_promotion_events(day, source_quality=quality)
    assert [row["scanner_promotion_id"] for row in rows["005930"]] == ["PROMO-1"]
    assert quality["status"] == "complete"
    assert quality["counts_complete"] is True
    assert quality["scanner_candidate_count"] == quality["scanner_valid_count"] == 1
    assert quality["scanner_excluded_count"] == 0
    assert quality["raw_row_count"] == 1
    assert quality["scanner_by_venue_session"] == {"KRX|KRX_REGULAR": 1}
    assert quality["scanner_by_stage"] == {
        "scalping_scanner_candidate_promoted": {"raw": 1, "valid": 1, "excluded": 0}
    }
    assert len(quality["source_generation_sha256"]) == 64
    assert len(quality["parts"][0]["physical_representations"]) == (2 if representation == "both" else 1)
    assert quality["parts"][0]["source_content_sha256"] == report_mod.hashlib.sha256(raw).hexdigest()
    assert quality["parts"][0]["archive_receipt"]["status"] == (
        "not_applicable" if representation == "plain" else "verified_logical_content"
    )


@pytest.mark.parametrize("late_compressed", [False, True])
def test_scanner_reader_merges_late_part_once_and_keeps_scale_in_projection(
    monkeypatch, tmp_path, late_compressed,
):
    monkeypatch.setattr(report_mod, "_PIPELINE_EVENTS_DIR", tmp_path)
    day = "2026-09-23"
    promoted = {"stage": "scalping_scanner_candidate_promoted",
                "emitted_at": f"{day}T09:00:00+09:00", "stock_code": "005930",
                "fields": {"scanner_promotion_id": "PROMO-1"}}
    scale_in = {"stage": "scale_in_order_submitted", "emitted_at": f"{day}T10:00:00+09:00",
                "stock_code": "005930", "strategy": "SCALPING",
                "fields": {"record_id": "1", "add_type": "AVG_DOWN",
                           "order_no": "BUY1", "request_qty": 4}}
    base = tmp_path / f"pipeline_events_{day}.jsonl"
    base.write_text("\n".join(map(json.dumps, [promoted, scale_in])) + "\n")
    late = tmp_path / f"pipeline_events_{day}.late.jsonl"
    late_content = "\n".join(map(json.dumps, [promoted, scale_in])) + "\n"
    if late_compressed:
        with gzip.open(f"{late}.gz", "wt") as handle:
            handle.write(late_content)
    else:
        late.write_text(late_content)
    projection = {"record_ids": {"1"}, "rows": []}
    quality = {}
    rows = report_mod._load_scanner_promotion_events(
        day, scale_in_projection=projection, source_quality=quality,
    )
    assert len(rows["005930"]) == 1
    assert len(projection["rows"]) == 1
    assert quality["raw_row_count"] == 4
    assert quality["scanner_candidate_count"] == 2
    assert quality["scanner_valid_count"] == quality["scanner_duplicate_count"] == 1
    assert len(quality["parts"]) == 2


def test_scanner_trade_does_not_match_different_known_venue_or_session():
    day = "2026-09-23"
    event = {"emitted_at": report_mod._parse_datetime(f"{day} 09:00:00"),
             "effective_venue": "NXT", "market_session_bucket": "NXT_REGULAR"}
    fact = {"strategy": "SCALPING", "position_tag": "SCANNER",
            "stock_code": "005930", "buy_time": f"{day} 09:05:00",
            "effective_venue": "KRX", "market_session_bucket": "KRX_REGULAR"}
    assert report_mod._select_scanner_event_for_trade(fact, {"005930": [event]}) is None
    assert report_mod._select_scanner_event_for_trade(
        {**fact, "effective_venue": "NXT", "market_session_bucket": "NXT_REGULAR"},
        {"005930": [event]},
    ) == event


def test_scanner_utc_event_clock_is_compared_in_kst(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "_PIPELINE_EVENTS_DIR", tmp_path)
    day = "2026-09-23"
    (tmp_path / f"pipeline_events_{day}.jsonl").write_text(json.dumps({
        "stage": "scalping_scanner_candidate_promoted",
        "emitted_at": "2026-09-23T00:00:00Z", "emitted_date": day,
        "storage_partition_date": day, "stock_code": "005930",
        "fields": {"scanner_promotion_id": "PROMO-UTC"},
    }) + "\n")
    source = report_mod._load_scanner_promotion_events(day)
    assert source["005930"][0]["emitted_at"].strftime("%H:%M") == "09:00"
    assert report_mod._select_scanner_event_for_trade({
        "strategy": "SCALPING", "position_tag": "SCANNER", "stock_code": "005930",
        "buy_time": "2026-09-23T00:05:00Z",
    }, source)["scanner_promotion_id"] == "PROMO-UTC"


def test_scanner_trade_explicit_promotion_id_wins_over_newer_same_symbol_event():
    day = "2026-09-23"
    old = {"emitted_at": report_mod._parse_datetime(f"{day} 09:00:00"),
           "scanner_promotion_id": "PROMO-OLD"}
    new = {"emitted_at": report_mod._parse_datetime(f"{day} 09:03:00"),
           "scanner_promotion_id": "PROMO-NEW"}
    fact = {"strategy": "SCALPING", "position_tag": "SCANNER",
            "stock_code": "005930", "buy_time": f"{day} 09:05:00",
            "scanner_expected_promotion_id": "PROMO-OLD"}
    assert report_mod._select_scanner_event_for_trade(
        fact, {"005930": [old, new]},
    ) == old


def test_scanner_reader_distinguishes_quarantine_empty_missing_and_corrupt(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "_PIPELINE_EVENTS_DIR", tmp_path)
    day = "2026-09-23"
    logical = tmp_path / f"pipeline_events_{day}.jsonl"
    quality = {}
    with pytest.raises(report_mod.FactSyncSourceError, match="scanner_pipeline_source_missing"):
        report_mod._load_scanner_promotion_events(day, source_quality=quality)
    assert quality["status"] == "source_missing"
    assert quality["counts_complete"] is False
    logical.write_text("")
    quality = {}
    assert not report_mod._load_scanner_promotion_events(day, source_quality=quality)
    assert quality["status"] == "valid_empty" and quality["raw_row_count"] == 0
    wrong_day = {"stage": "scalping_scanner_candidate_promoted",
                 "emitted_at": "2026-09-22T09:00:00+09:00", "stock_code": "005930",
                 "fields": {"scanner_promotion_id": "PROMO-OLD"}}
    logical.write_text(json.dumps(wrong_day) + "\n")
    quality = {}
    assert not report_mod._load_scanner_promotion_events(day, source_quality=quality)
    assert quality["status"] == "valid_empty"
    assert quality["scanner_candidate_count"] == quality["scanner_quarantined_count"] == 1
    assert quality["quarantine_reasons"] == {"emitted_date_invalid": 1}
    logical.write_text("{bad json}\n")
    quality = {}
    with pytest.raises(report_mod.FactSyncSourceError, match="scanner_pipeline_source_invalid"):
        report_mod._load_scanner_promotion_events(day, source_quality=quality)
    assert quality["status"] == "source_blocked"
    assert quality["counts_complete"] is False
    logical.unlink()
    (tmp_path / f"{logical.name}.gz").write_bytes(b"bad gzip")
    with pytest.raises(report_mod.FactSyncSourceError, match="scanner_pipeline_source_invalid"):
        report_mod._load_scanner_promotion_events(day)


def test_scanner_reader_rejects_conflicting_plain_gzip_and_promotion_identity(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "_PIPELINE_EVENTS_DIR", tmp_path)
    day = "2026-09-23"
    logical = tmp_path / f"pipeline_events_{day}.jsonl"
    row = {"stage": "scalping_scanner_candidate_promoted",
           "emitted_at": f"{day}T09:00:00+09:00", "stock_code": "005930",
           "fields": {"scanner_promotion_id": "PROMO-1", "scanner_promotion_reason": "first"}}
    logical.write_text(json.dumps(row) + "\n")
    changed = {**row, "fields": {**row["fields"], "scanner_promotion_reason": "conflict"}}
    with gzip.open(f"{logical}.gz", "wt") as handle:
        handle.write(json.dumps(changed) + "\n")
    with pytest.raises(report_mod.FactSyncSourceError, match="plain_gzip_conflict"):
        report_mod._load_scanner_promotion_events(day)
    (tmp_path / f"{logical.name}.gz").unlink()
    logical.write_text("\n".join(map(json.dumps, [row, changed])) + "\n")
    with pytest.raises(report_mod.FactSyncSourceError, match="promotion_identity_conflict"):
        report_mod._load_scanner_promotion_events(day)


def test_scanner_reader_rejects_archive_receipt_with_different_logical_sha(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "_PIPELINE_EVENTS_DIR", tmp_path)
    day = "2026-09-23"
    logical = tmp_path / f"pipeline_events_{day}.jsonl"
    with gzip.open(f"{logical}.gz", "wt") as handle:
        handle.write(json.dumps({"stage": "scalping_scanner_candidate_promoted",
                                 "emitted_at": f"{day}T09:00:00+09:00",
                                 "stock_code": "005930",
                                 "fields": {"scanner_promotion_id": "PROMO-1"}}) + "\n")
    receipt = tmp_path / f"{logical.name}.gz.archive_receipt.json"
    receipt.write_text(json.dumps({"schema": "pipeline_raw_archive_identity_v1",
                                   "logical_path": str(logical),
                                   "logical_content_sha256": "0" * 64}))
    with pytest.raises(report_mod.FactSyncSourceError, match="archive_receipt_generation_mismatch"):
        report_mod._load_scanner_promotion_events(day)


@pytest.mark.parametrize("source_kind", ["missing", "valid_empty"])
def test_scanner_source_gap_preserves_prior_facts_and_records_reason(
    monkeypatch, tmp_path, source_kind,
):
    from src.engine.scalping import scale_in_split_order_plan

    day = "2026-09-23"
    events = tmp_path / "pipeline_events"
    events.mkdir()
    monkeypatch.setattr(report_mod, "_PIPELINE_EVENTS_DIR", events)
    monkeypatch.setattr(report_mod, "_FACT_SYNC_STATUS_DIR", tmp_path / "status")
    monkeypatch.setattr(scale_in_split_order_plan, "_query_actual_fill_inventory", lambda _: [])
    monkeypatch.setattr(report_mod, "build_trade_review_report", lambda **_kwargs: {
        "meta": {"warnings": []},
        "sections": {"recent_trades": [{
            "id": 1, "rec_date": day, "code": "005930", "status": "HOLDING",
            "strategy": "SCALPING", "position_tag": "SCANNER",
            "buy_price": 1000, "buy_qty": 1, "buy_time": f"{day} 09:05:00",
        }]},
    })
    if source_kind == "valid_empty":
        (events / f"pipeline_events_{day}.jsonl").write_text("")
    executed = []

    class _Query:
        def filter(self, *_args):
            return self

        def count(self):
            return 7

    class _Session:
        def query(self, *_args):
            return _Query()

        def execute(self, statement):
            executed.append(statement)

    @contextmanager
    def _session():
        yield _Session()

    monkeypatch.setattr(report_mod._DB, "init_db", lambda: None)
    monkeypatch.setattr(report_mod._DB, "get_session", _session)
    with pytest.raises(report_mod.FactSyncSourceError):
        report_mod.sync_trade_performance_for_date(day)
    assert executed == []
    receipt = json.loads(
        (tmp_path / "status" / f"strategy_position_fact_sync_{day}.status.json").read_text()
    )
    assert receipt["status"] == "source_blocked"
    assert receipt["consumer_ready"] is False
    assert receipt["prior_fact_count"] == 7
    assert receipt["scanner_source_quality"]["status"] == (
        "source_missing" if source_kind == "missing" else "valid_empty"
    )
    if source_kind == "valid_empty":
        assert receipt["scanner_source_quality"]["scanner_unmatched_fact_count"] == 1
        assert receipt["issues"] == ["scanner_lineage_unmatched:1"]
    else:
        assert "scanner_pipeline_source_missing" in receipt["issues"][0]


def test_scanner_gzip_lineage_reaches_report_fallback_consumer(monkeypatch, tmp_path):
    day = "2026-09-23"
    monkeypatch.setattr(report_mod, "_PIPELINE_EVENTS_DIR", tmp_path)
    logical = tmp_path / f"pipeline_events_{day}.jsonl"
    with gzip.open(f"{logical}.gz", "wt") as handle:
        handle.write(json.dumps({
            "stage": "scalping_scanner_candidate_promoted",
            "emitted_at": f"{day}T09:00:00+09:00", "stock_code": "005930",
            "fields": {"scanner_promotion_id": "PROMO-1",
                       "scanner_promotion_reason": "price_jump_start_acceleration"},
        }) + "\n")
    monkeypatch.setattr(report_mod, "build_trade_review_report", lambda **_kwargs: {
        "meta": {"warnings": []}, "sections": {"recent_trades": [{
            "id": 1, "rec_date": day, "code": "005930", "name": "Samsung",
            "status": "HOLDING", "strategy": "SCALPING", "position_tag": "SCANNER",
            "buy_price": 1000, "buy_qty": 1, "buy_time": f"{day} 09:05:00",
        }]},
    })

    @contextmanager
    def _broken_session():
        raise RuntimeError("db unavailable")
        yield None

    monkeypatch.setattr(report_mod._DB, "init_db", lambda: None)
    monkeypatch.setattr(report_mod._DB, "get_session", _broken_session)
    payload = report_mod.build_strategy_position_performance_report(day)
    scanner = payload["sections"]["scanner_discovery_rows"]
    assert len(scanner) == 1
    assert scanner[0]["scanner_discovery_type"] == "price_jump_acceleration"
    assert scanner[0]["provenance_matched_count"] == 1


def test_fact_consumer_preserves_actual_cost_revision_and_configured_rate_separately(monkeypatch):
    from src.engine.sniper_trade_review_report import completed_census_manifest
    day = "2026-10-08"
    row = {"id": 1, "rec_date": day, "code": "123456", "status": "COMPLETED",
        "strategy": "SCALPING", "position_tag": "SCALP_BASE", "profit_rate": 0.8,
        "buy_price": 10000, "buy_qty": 2, "buy_time": day + " 10:00:00",
        "sell_price": 10100, "sell_time": day + " 10:01:01"}
    projected = {**row, "completion_observed_date": day, "terminal_population_scope": "real_record_bound",
        "strict_completion_status": "eligible", "broker_actual_cost_observed": True,
        "broker_actual_fees_taxes_krw": 10, "realized_pnl_krw": 190, "profit_rate": 0.95,
        "realized_pnl_krw_source": "broker_actual_fee_reconciled",
        "actual_cost_reconciliation": {"status": "actual_cost_reconciled", "revision": 2},
        "exit_signal": {"inferred": False, "binding_status": "same_order_generation"}}
    generation = {"sha256": "b" * 64, "count": 1}
    report = {"date": day, "meta": {"warnings": [], "sell_completed_event_ids": [1],
        "actual_cost_source_generation": generation}, "metrics": {"canonical_completed_trades": 1},
        "sections": {"recent_trades": [row], "completed_trade_projection": [projected]}}
    report["meta"]["completed_census_manifest"] = completed_census_manifest(report)
    monkeypatch.setattr(report_mod, "build_trade_review_report", lambda **_kw: report)
    facts, warnings = report_mod._build_trade_fact_rows(day)
    assert warnings == []
    assert facts[0]["realized_pnl_krw"] == 190
    assert facts[0]["profit_rate"] == 0.95
    assert facts[0]["actual_cost_reconciliation_status"] == "actual_cost_reconciled"
    assert facts[0]["actual_cost_source_generation"] == generation
    assert row["profit_rate"] == 0.8
