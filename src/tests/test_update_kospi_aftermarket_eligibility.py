from datetime import date, datetime
from zoneinfo import ZoneInfo
import logging
import pytest

from src.database.db_manager import DBManager
from src.database.models import Base
from src.utils import kiwoom_utils, update_kospi


KST = ZoneInfo("Asia/Seoul")


@pytest.fixture(autouse=True)
def isolate_eod_logger(monkeypatch):
    # Regression failures and synthetic censuses must not enter production logs.
    monkeypatch.setattr(update_kospi, "logger", logging.getLogger("EodSourceFixture"))


def test_ka10099_raw_eligibility_preserves_pagination_and_provenance(monkeypatch):
    calls = []

    def fake_fetch(**kwargs):
        calls.append(kwargs)
        market = kwargs["payload"]["mrkt_tp"]
        rows = []
        if market == "0":
            rows = [
                {
                    "return_code": 0,
                    "list": [
                        {
                            "code": "005930",
                            "auditInfo": "정상",
                            "state": "증거금1100%",
                            "orderWarning": "0",
                            "marketCode": "0",
                            "nxtEnable": "Y",
                        }
                    ],
                },
                {"return_code": 0, "list": []},
            ]
        return rows, {
            "page_count": len(rows),
            "last_http_status_code": 200,
            "request_attempt_count": len(rows),
            "continuous_next_key_missing": False,
            "continuous_page_limit_reached": False,
        }

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", fake_fetch)
    observed_at = datetime(2026, 9, 11, 20, 5, tzinfo=KST)

    rows, meta = kiwoom_utils.get_stock_eligibility_map_ka10099(
        "fake-token",
        ["005930"],
        mrkt_tps=("0",),
        trade_date=date(2026, 9, 11),
        observed_at_kst=observed_at,
    )

    assert calls[0]["api_id"] == "ka10099"
    assert calls[0]["use_continuous"] is True
    assert calls[0]["return_meta"] is True
    assert meta["complete"] is True
    assert meta["page_count"] == 2
    row = rows["005930"]
    assert row["nxt_eligible"] is True
    assert row["krx_aftermarket_eligible"] is None
    assert row["audit_info"] == "정상"
    assert row["stock_state"] == "증거금1100%"
    assert row["order_warning"] == "0"
    assert row["market_code"] == "0"
    assert row["source_api_id"] == "ka10099"
    assert row["source_revision"] == meta["eligibility_source_revision"]
    assert row["observed_at_kst"] == "2026-09-11T20:05:00+09:00"
    assert len(row["payload_sha256"]) == 64
    assert "krx_aftermarket_eligibility_unknown" in row["blocked_reasons"]


def test_ka10099_incomplete_page_contract_blocks_entire_snapshot(monkeypatch):
    def fake_fetch(**kwargs):
        return [
            {
                "return_code": 0,
                "list": [
                    {
                        "code": "005930",
                        "auditInfo": "정상",
                        "state": "정상",
                        "orderWarning": "0",
                        "marketCode": "0",
                        "nxtEnable": "Y",
                    }
                ],
            }
        ], {
            "page_count": 1,
            "last_http_status_code": 200,
            "continuous_next_key_missing": True,
        }

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", fake_fetch)

    rows, meta = kiwoom_utils.get_stock_eligibility_map_ka10099(
        "fake-token",
        ["005930"],
        mrkt_tps=("0",),
        trade_date=date(2026, 9, 11),
        observed_at_kst=datetime(2026, 9, 11, 20, 5, tzinfo=KST),
    )

    assert meta["complete"] is False
    assert rows["005930"]["quality_state"] == "UNKNOWN"
    assert rows["005930"]["eligible_venues_json"] == []
    assert "official_source_snapshot_incomplete" in rows["005930"]["blocked_reasons"]


def test_ka10099_missing_symbol_does_not_invalidate_received_symbol(monkeypatch):
    def fake_fetch(**kwargs):
        return [
            {
                "return_code": 0,
                "list": [
                    {
                        "code": "005930",
                        "auditInfo": "정상",
                        "state": "정상",
                        "orderWarning": "0",
                        "marketCode": "0",
                        "nxtEnable": "Y",
                    }
                ],
            }
        ], {
            "page_count": 1,
            "last_http_status_code": 200,
            "continuous_next_key_missing": False,
            "continuous_page_limit_reached": False,
        }

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", fake_fetch)

    rows, meta = kiwoom_utils.get_stock_eligibility_map_ka10099(
        "fake-token",
        ["005930", "000660"],
        mrkt_tps=("0",),
        trade_date=date(2026, 9, 11),
        observed_at_kst=datetime(2026, 9, 11, 20, 5, tzinfo=KST),
    )

    assert meta["complete"] is True
    assert meta["status"] == "partial"
    assert meta["received_code_count"] == 1
    assert meta["missing_codes"] == ["000660"]
    assert rows["005930"]["quality_state"] == "PARTIAL"
    assert rows["005930"]["complete"] is True
    assert rows["000660"]["quality_state"] == "UNKNOWN"
    assert "official_source_row_missing" in rows["000660"]["blocked_reasons"]


def test_eod_collection_stores_nullable_aftermarket_and_uses_legacy_nxt_fallback(
    monkeypatch, tmp_path
):
    db = DBManager(f"sqlite:///{tmp_path / 'eligibility.sqlite3'}")
    Base.metadata.create_all(db.engine)
    with db.engine.begin() as conn:
        conn.exec_driver_sql(
            "INSERT INTO daily_stock_quotes "
            "(quote_date, stock_code, is_nxt) VALUES ('2026-09-10', '000660', 1)"
        )

    def fake_source(*args, **kwargs):
        return {
            "005930": {
                "trade_date": "2026-09-11",
                "stock_code": "005930",
                "krx_regular_eligible": True,
                "nxt_eligible": True,
                "krx_aftermarket_eligible": None,
                "eligible_venues_json": ["NXT"],
                "audit_info": "정상",
                "stock_state": "정상",
                "order_warning": "0",
                "market_code": "0",
                "source_api_id": "ka10099",
                "source_revision": "234560d213acd8871ae344b5481aecd2f30287fa",
                "observed_at_kst": "2026-09-11T20:05:00+09:00",
                "payload_sha256": "a" * 64,
                "quality_state": "PARTIAL",
                "blocked_reasons": ["krx_aftermarket_eligibility_unknown"],
                "complete": False,
                "status": "partial",
            },
            "000660": {
                "trade_date": "2026-09-11",
                "stock_code": "000660",
                "krx_regular_eligible": None,
                "nxt_eligible": None,
                "krx_aftermarket_eligible": None,
                "eligible_venues_json": [],
                "source_api_id": "ka10099",
                "source_revision": "234560d213acd8871ae344b5481aecd2f30287fa",
                "observed_at_kst": "2026-09-11T20:05:00+09:00",
                "payload_sha256": None,
                "quality_state": "UNKNOWN",
                "blocked_reasons": ["official_source_row_missing"],
                "complete": False,
                "status": "partial",
            },
        }, {"api_id": "ka10099", "status": "partial", "complete": False}

    monkeypatch.setattr(
        kiwoom_utils, "get_stock_eligibility_map_ka10099", fake_source
    )
    monkeypatch.setattr(
        db,
        "get_latest_is_nxt_map",
        lambda codes: {code: code == "000660" for code in codes},
    )

    with db.get_session() as session:
        nxt_map, summary = update_kospi._collect_and_store_market_eligibility(
            db,
            session,
            token="fake-token",
            stock_codes=["005930", "000660"],
            trade_date=date(2026, 9, 11),
        )

    assert summary["stored_count"] == 2
    assert summary["quality_counts"] == {"UNKNOWN": 2}
    assert nxt_map == {"000660": True, "005930": False}
    stored = db.get_security_market_eligibility("005930", "2026-09-11")
    assert stored is not None
    assert stored["nxt_eligible"] is True
    assert stored["krx_aftermarket_eligible"] is None
    assert stored["quality_state"] == "UNKNOWN"
    assert "aftermarket_eligibility_source_incomplete" in stored[
        "blocked_reasons_json"
    ]


def test_daily_quote_upsert_preserves_unreceived_history_and_refreshes_received():
    import pandas as pd
    from sqlalchemy import create_engine, select
    from src.database.models import DailyStockQuote

    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    table = DailyStockQuote.__table__
    with engine.begin() as conn:
        conn.execute(table.insert(), [
            {'quote_date': date(2026, 10, 1), 'stock_code': '005930', 'close_price': 10.0},
            {'quote_date': date(2026, 9, 30), 'stock_code': '005930', 'close_price': 9.0},
            {'quote_date': date(2026, 10, 1), 'stock_code': '000660', 'close_price': 20.0},
        ])
        frame = pd.DataFrame([
            {'quote_date': date(2026, 10, 1), 'stock_code': '005930', 'close_price': 11.0},
            {'quote_date': date(2026, 10, 2), 'stock_code': '005930', 'close_price': 12.0},
        ])
        assert update_kospi._upsert_daily_quote_batch(conn, frame) == 2
        assert update_kospi._upsert_daily_quote_batch(conn, frame) == 2
        rows = conn.execute(select(table.c.quote_date, table.c.stock_code, table.c.close_price)).all()
    assert set(rows) == {
        (date(2026, 9, 30), '005930', 9.0),
        (date(2026, 10, 1), '005930', 11.0),
        (date(2026, 10, 2), '005930', 12.0),
        (date(2026, 10, 1), '000660', 20.0),
    }


def test_daily_quote_batch_rejects_duplicate_identity_before_writes():
    import pandas as pd
    import pytest
    from sqlalchemy import create_engine, select
    from src.database.models import DailyStockQuote

    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    frame = pd.DataFrame([{'quote_date': date(2026, 10, 2), 'stock_code': '005930'}] * 2)
    with engine.begin() as conn:
        with pytest.raises(ValueError, match='duplicate_identity'):
            update_kospi._upsert_daily_quote_batch(conn, frame)
        assert conn.execute(select(DailyStockQuote.__table__)).all() == []


def test_daily_quote_batch_rolls_back_earlier_chunks_on_late_failure(monkeypatch):
    import pandas as pd
    import pytest
    from sqlalchemy import create_engine, select, event
    from src.database.models import DailyStockQuote

    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    monkeypatch.setattr(update_kospi, 'BULK_CHUNKSIZE', 1)
    calls = []

    @event.listens_for(engine, 'before_cursor_execute')
    def fail_second_insert(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith('INSERT INTO daily_stock_quotes'):
            calls.append(statement)
            if len(calls) == 2:
                raise RuntimeError('synthetic_write_failure')

    frame = pd.DataFrame([
        {'quote_date': date(2026, 10, 1), 'stock_code': '005930'},
        {'quote_date': date(2026, 10, 2), 'stock_code': '005930'},
    ])
    with pytest.raises(RuntimeError, match='synthetic_write_failure'):
        with engine.begin() as conn:
            update_kospi._upsert_daily_quote_batch(conn, frame)
    with engine.connect() as conn:
        assert conn.execute(select(DailyStockQuote.__table__)).all() == []


def test_failed_eod_source_does_not_run_recommendation(monkeypatch, tmp_path):
    monkeypatch.setattr(update_kospi, 'update_kospi_data', lambda: {
        'status': 'failed', 'reason': 'target_date_rows_missing'})
    monkeypatch.setattr(update_kospi, 'STATUS_DIR', tmp_path)
    monkeypatch.setattr(update_kospi, '_load_latest_quote_state', lambda: {})
    monkeypatch.setattr(update_kospi.subprocess, 'run', lambda *a, **k: (_ for _ in ()).throw(
        AssertionError('downstream must not run')))
    result = update_kospi.run_update_kospi_chain()
    assert result['status'] == 'failed'
    assert result['failed_steps'] == ['update_kospi_data']
    assert len(result['steps']) == 1


def test_eod_downstream_failure_is_not_a_success_with_warning(monkeypatch):
    monkeypatch.setattr(update_kospi, '_load_latest_quote_state', lambda: {})
    result = update_kospi._build_update_kospi_status('2026-10-02', 'start', [
        {'name': 'update_kospi_data', 'status': 'completed'},
        {'name': 'recommend_daily_v2', 'status': 'failed'},
    ])
    assert result['status'] == 'failed'
    assert result['failed_steps'] == ['recommend_daily_v2']


def test_daily_quote_postgresql_statement_preserves_keys_and_nulls():
    import pandas as pd
    from types import SimpleNamespace
    from sqlalchemy.dialects import postgresql

    statements = []
    conn = SimpleNamespace(dialect=postgresql.dialect(), execute=statements.append)
    frame = pd.DataFrame([{'quote_date': date(2026, 10, 2), 'stock_code': '005930',
                          'close_price': 10.0, 'foreign_net': float('nan')}])
    assert update_kospi._upsert_daily_quote_batch(conn, frame) == 1
    compiled = statements[0].compile(dialect=conn.dialect)
    assert 'ON CONFLICT (quote_date, stock_code) DO UPDATE SET' in str(compiled)
    assert 'DELETE' not in str(compiled)
    assert compiled.params['foreign_net_m0'] is None
    assert compiled.params['quote_date_m0'] == date(2026, 10, 2)


def test_eod_source_census_distinguishes_empty_stale_and_partial(monkeypatch):
    import pandas as pd
    from sqlalchemy import create_engine
    from types import SimpleNamespace
    from contextlib import nullcontext

    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    monkeypatch.setattr(update_kospi, 'DBManager', lambda: SimpleNamespace(
        engine=engine, init_db=lambda: None, get_session=lambda: nullcontext()))
    monkeypatch.setattr(update_kospi, 'EventBus', lambda: SimpleNamespace(publish=lambda *a: None))
    monkeypatch.setattr(update_kospi.kiwoom_utils, 'is_trading_day', lambda: (True, 'fixture'))
    monkeypatch.setattr(update_kospi.kiwoom_utils, 'get_kiwoom_token', lambda: 'fixture-token')
    monkeypatch.setattr(update_kospi.fdr, 'StockListing', lambda *a: pd.DataFrame(
        [{'Market': 'KOSPI', 'Code': '005930'}, {'Market': 'KOSPI', 'Code': '000660'},
         {'Market': 'KOSPI', 'Code': '00088K'}]))
    monkeypatch.setattr(update_kospi, '_collect_and_store_market_eligibility',
                        lambda *a, **k: ({}, {'status': 'pass', 'stored_count': 2}))
    monkeypatch.setattr(update_kospi, '_today_str', lambda: '2026-10-02')
    monkeypatch.setattr(update_kospi.time, 'sleep', lambda *a: None)
    monkeypatch.setattr(update_kospi, 'process_and_save_stock', lambda *a, **k: pd.DataFrame())
    empty = update_kospi.update_kospi_data()
    assert empty['status'] == 'failed'
    assert empty['reason'] == 'no_collected_rows'
    assert empty['unreceived_codes'] == ['000660', '005930']
    assert empty['total_count'] == 2
    assert empty['excluded_symbol_identities'] == [{
        'raw_code': '00088K', 'canonical_code': '00088K',
        'reason': 'unsupported_equity_namespace'}]

    observed_date = date(2026, 10, 1)

    def received(code, *args, **kwargs):
        if code == '000660':
            return pd.DataFrame()
        return pd.DataFrame([{'quote_date': observed_date, 'stock_code': code, 'close_price': 10.0}])

    monkeypatch.setattr(update_kospi, 'process_and_save_stock', received)
    stale = update_kospi.update_kospi_data()
    assert stale['status'] == 'failed'
    assert stale['reason'] == 'target_date_rows_missing'
    assert stale['target_date_symbol_count'] == 0
    observed_date = date(2026, 10, 2)
    partial = update_kospi.update_kospi_data()
    assert partial['status'] == 'completed_with_warnings'
    assert partial['target_date_symbol_count'] == 1
    assert partial['missing_target_date_codes'] == ['000660']
    assert partial['inserted_rows'] == 1


def test_eod_normalization_never_collapses_instrument_namespaces():
    assert update_kospi._normalize_stock_code('00088K') == '00088K'
    assert update_kospi._normalize_stock_code('A005930_AL') == '005930'
    assert update_kospi._normalize_stock_code('005930_NX') == '005930'
    assert update_kospi._normalize_stock_code('1234567') == '1234567'
