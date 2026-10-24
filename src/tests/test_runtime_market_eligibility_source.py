"""Startup listing preparation and canonical persistence without provider calls."""
from datetime import date, datetime, timedelta
from contextlib import contextmanager
import json
from pathlib import Path
import threading
from types import SimpleNamespace

import pytest

from src.database.db_manager import DBManager
from src.database.models import Base
from src.engine.infrastructure import market_eligibility_source as source
from src.utils import kiwoom_utils as K


def item(code='005930', nxt='Y', **changes):
    return dict(code=code, nxtEnable=nxt, auditInfo='정상', state='증거금100%',
                orderWarning='0', marketCode='0', **changes)


def market_response(rows):
    return [dict(return_code=0, list=rows)], dict(
        last_http_status_code=200, request_attempt_count=1,
        continuous_next_key_missing=False, continuous_page_limit_reached=False)


@pytest.fixture
def db(tmp_path):
    value = DBManager(f"sqlite:///{tmp_path / 'source.sqlite3'}")
    Base.metadata.create_all(value.engine)
    return value


def install_pages(monkeypatch, *, rows=None):
    calls = []
    def fetch(**kwargs):
        calls.append(kwargs)
        market = kwargs['payload']['mrkt_tp']
        return market_response((rows or {}).get(market, [item('005930' if market == '0' else '036930')]))
    monkeypatch.setattr(K, 'fetch_kiwoom_api_continuous', fetch)
    return calls


def runtime(tmp_path, *, now=None, **kwargs):
    return source.RuntimeMarketEligibilitySource(
        tmp_path / 'receipts', now=now or (lambda: datetime(2026, 10, 14, 18, 45, tzinfo=source.KST)),
        calendar=lambda day: True, token=lambda: 'fixture-token', log=lambda message: None, **kwargs)


def test_all_listing_mode_bounds_and_empty_request_stays_no_call(monkeypatch):
    calls = install_pages(monkeypatch)
    assert K.get_stock_eligibility_map_ka10099('fixture', [], runtime_prepare=True)[0] == {}
    assert calls == []
    rows, meta = K.get_stock_eligibility_map_ka10099('fixture', None, runtime_prepare=True,
        trade_date='2026-10-14', observed_at_kst=datetime(2026, 10, 14, 18, tzinfo=source.KST))
    assert set(rows) == {'005930', '036930'}
    assert meta['complete'] and meta['requested_scope'] == 'all_listings'
    assert [call['payload'] for call in calls] == [{'mrkt_tp': '0'}, {'mrkt_tp': '10'}]
    for call in calls:
        assert call['api_id'] == 'ka10099' and call['use_continuous'] and call['return_meta']
        assert call['max_retries'] == 1 and call['max_pages'] == 8
        assert call['request_timeout'] == (1.0, 2.0)
        assert call['read_rate_max_wait_sec'] == 1.0
        assert call['request_class'] == K.REQUEST_CLASS_SOURCE_ONLY
    assert all(row['source_revision'] == '953e5dbff123f437ab4d11a78a95191a685eb51f' for row in rows.values())


@pytest.mark.parametrize('value,expected', [('Y', True), ('N', False), ('y', None), ('1', None), ('', None)])
def test_runtime_only_explicit_eligibility_values(monkeypatch, value, expected):
    install_pages(monkeypatch, rows={'0': [item(nxt=value)]})
    rows, _ = K.get_stock_eligibility_map_ka10099('fixture', None, runtime_prepare=True)
    assert rows['005930']['nxt_eligible'] is expected
    assert rows['005930']['krx_aftermarket_eligible'] is True
    assert rows['005930']['quality_state'] == ('PARTIAL' if expected is None else 'VALID')


def test_runtime_conflict_cannot_be_erased_by_later_duplicate(monkeypatch):
    install_pages(monkeypatch, rows={'0': [item(nxt='Y'), item(nxt='N'), item(nxt='N')]})
    rows, _ = K.get_stock_eligibility_map_ka10099('fixture', None, runtime_prepare=True)
    assert rows['005930']['quality_state'] == 'CONFLICT'
    assert 'official_source_conflict' in rows['005930']['blocked_reasons']


@pytest.mark.parametrize('failure', ['next_key', 'page_limit', 'http', 'business', 'no_code', 'no_list', 'empty', 'no_meta'])
def test_runtime_incomplete_market_keeps_every_received_row_unknown(monkeypatch, failure):
    def fetch(**kwargs):
        responses, meta = market_response([item('005930' if kwargs['payload']['mrkt_tp'] == '0' else '036930')])
        if kwargs['payload']['mrkt_tp'] == '10':
            if failure == 'next_key': meta['continuous_next_key_missing'] = True
            elif failure == 'page_limit': meta['continuous_page_limit_reached'] = True
            elif failure == 'http': meta['last_http_status_code'] = 500
            elif failure == 'business': responses[0]['return_code'] = 1
            elif failure == 'no_code': responses[0].pop('return_code')
            elif failure == 'no_list': responses[0].pop('list')
            elif failure == 'empty': responses[0]['list'] = []
            elif failure == 'no_meta': meta = {}
        return responses, meta
    monkeypatch.setattr(K, 'fetch_kiwoom_api_continuous', fetch)
    rows, meta = K.get_stock_eligibility_map_ka10099('fixture', None, runtime_prepare=True)
    assert meta['complete'] is False
    assert rows['005930']['quality_state'] == 'UNKNOWN'
    assert all(row['complete'] is False for row in rows.values())


def test_current_day_storage_cache_and_next_day_collection(monkeypatch, db, tmp_path):
    calls = install_pages(monkeypatch)
    clock = [datetime(2026, 10, 14, 18, 45, tzinfo=source.KST)]
    owner = runtime(tmp_path, now=lambda: clock[0])
    first = owner.tick(db)
    assert first['status'] == 'pass' and first['stored_count'] == 2
    row = db.get_security_market_eligibility('005930', clock[0].date())
    assert row['quality_state'] == 'VALID' and row['nxt_eligible'] is True
    assert row['krx_aftermarket_eligible'] is True
    assert row['blocked_reasons_json'] == []
    assert len(row['payload_sha256']) == 64 and row['source_api_id'] == 'ka10099'
    assert owner.tick(db)['cache_hit'] is True and len(calls) == 2
    clock[0] += timedelta(days=1)
    assert owner.tick(db)['status'] == 'pass' and len(calls) == 4
    receipts = sorted((tmp_path / 'receipts').glob('*/latest.json'))
    assert len(receipts) == 2
    assert all(json.loads(path.read_text())['authority'] == 'venue_listing_source_only' for path in receipts)
    original = json.loads(receipts[0].read_text())['source_rows']['005930']
    assert original['payload_sha256'] == row['payload_sha256']
    assert original['observed_at_kst'].startswith('2026-10-14T18:45:00')


def test_collector_to_timezone_preserving_db_main_adapter_and_nxt_preflight(monkeypatch, tmp_path):
    # PostgreSQL preserves timezone-aware ORM datetimes. SQLite strips the
    # offset, so capture the actual merged ORM values for this consumer proof.
    from src.engine import sniper_state_handlers as handlers
    from src.trading.market import session_contract as contract
    records = {}
    def merge(model):
        records[model.stock_code] = {
            column.name: getattr(model, column.name) for column in model.__table__.columns}
    @contextmanager
    def session():
        yield SimpleNamespace(merge=merge, query=lambda *_: SimpleNamespace(
            filter=lambda *_: SimpleNamespace(all=lambda: [])))
    db = SimpleNamespace(get_session=session,
        get_security_market_eligibility=lambda code, day: records.get(code))
    install_pages(monkeypatch)
    owner = runtime(tmp_path)
    assert owner.tick(db)['status'] == 'pass'
    monkeypatch.setattr(handlers, 'DB', db)
    now = datetime(2026, 10, 14, 18, 45, 1, tzinfo=source.KST)
    evidence = handlers._entry_order_venue_eligibility('005930', now=now)
    assert evidence.quality_state == 'VALID'
    assert evidence.source_trade_date == '2026-10-14'
    context = contract.resolve_market_session(now)
    nxt = contract.resolve_order_type_preflight(context, 'NXT', 'buy', '3', eligibility=evidence)
    assert nxt.allowed and nxt.effective_order_type == '6'
    assert contract.resolve_order_type_preflight(context, 'SOR', 'buy', '3', eligibility=evidence).allowed
    records['005930']['quality_state'] = 'UNKNOWN'
    assert not contract.resolve_order_type_preflight(context, 'SOR', 'buy', '3',
        eligibility=handlers._entry_order_venue_eligibility('005930', now=now)).allowed


def test_same_day_complete_refresh_invalidates_missing_old_row_and_recovers(monkeypatch, db, tmp_path):
    install_pages(monkeypatch)
    first = runtime(tmp_path / 'first').tick(db)
    assert first['status'] == 'pass'
    original = db.get_security_market_eligibility('005930', '2026-10-14')
    install_pages(monkeypatch, rows={'0': [item('009540')]})
    missing = runtime(tmp_path / 'restart').tick(db)
    row = db.get_security_market_eligibility('005930', '2026-10-14')
    assert missing['status'] == 'pass' and row['quality_state'] == 'UNKNOWN'
    assert row['nxt_eligible'] is None and row['payload_sha256'] is None
    assert 'official_source_row_missing' in row['blocked_reasons_json']
    assert missing['superseded_missing_rows']['005930']['payload_sha256'] == original['payload_sha256']
    immutable = next((tmp_path / 'restart/receipts/2026-10-14').glob('*-1.json'))
    assert json.loads(immutable.read_text())['superseded_missing_rows']['005930']['nxt_eligible'] is True
    install_pages(monkeypatch)
    recovered = runtime(tmp_path / 'another-restart').tick(db)
    assert recovered['status'] == 'pass'
    row = db.get_security_market_eligibility('005930', '2026-10-14')
    assert row['quality_state'] == 'VALID' and row['nxt_eligible'] is True
    assert row['blocked_reasons_json'] == []


def test_failures_retry_on_later_ticks_with_daily_limit(db, tmp_path):
    attempts, logs, clock = [], [], [0.0]
    def fail(*args, **kwargs):
        attempts.append(True)
        raise TimeoutError('private body must not be persisted')
    owner = runtime(tmp_path, fetch=fail, monotonic=lambda: clock[0])
    assert owner.tick(db)['status'] == 'fail'
    assert owner.tick(db)['retry_deferred'] and len(attempts) == 1
    for _ in range(5):
        clock[0] += source.RETRY_INTERVAL_SECONDS
        owner.tick(db)
    assert len(attempts) == source.MAX_DAILY_ATTEMPTS == 3
    records = list((tmp_path / 'receipts').glob('*/*.json'))
    assert len(records) == 4
    assert all('private body' not in path.read_text() for path in records)


def test_incomplete_source_is_stored_unknown_and_not_cached(monkeypatch, db, tmp_path):
    def fetch(**kwargs):
        responses, meta = market_response([item()])
        meta['continuous_page_limit_reached'] = True
        return responses, meta
    monkeypatch.setattr(K, 'fetch_kiwoom_api_continuous', fetch)
    owner = runtime(tmp_path)
    assert owner.tick(db)['status'] == 'partial'
    row = db.get_security_market_eligibility('005930', '2026-10-14')
    assert row['quality_state'] == 'UNKNOWN'
    assert 'aftermarket_eligibility_source_incomplete' in row['blocked_reasons_json']
    assert owner.tick(db)['retry_deferred'] is True


def test_date_rollover_during_collection_never_publishes_previous_day(db, tmp_path):
    clock = [datetime(2026, 10, 14, 23, 59, tzinfo=source.KST)]
    def fetch(*args, **kwargs):
        clock[0] += timedelta(days=1)
        return {}, {'complete': True}
    owner = runtime(tmp_path, now=lambda: clock[0], fetch=fetch)
    result = owner.tick(db)
    assert result['status'] == 'fail'
    assert result.get('stored_count', 0) == 0


def test_concurrent_tick_has_single_owner(db, tmp_path):
    started, release = threading.Event(), threading.Event()
    calls = []
    def fetch(*args, **kwargs):
        calls.append(True)
        started.set()
        assert release.wait(3)
        return {}, {'complete': False}
    owner = runtime(tmp_path, fetch=fetch)
    worker = threading.Thread(target=owner.tick, args=(db,))
    worker.start()
    try:
        assert started.wait(3)
        assert owner.tick(db) == {'status': 'in_progress'}
        assert len(calls) == 1
    finally:
        release.set()
        worker.join(3)
    assert not worker.is_alive()


def test_closed_date_never_fetches_and_startup_hook_precedes_workers(tmp_path, db):
    owner = source.RuntimeMarketEligibilitySource(tmp_path, calendar=lambda day: False,
        token=lambda: pytest.fail('closed-date token call'))
    assert owner.tick(db)['status'] == 'not_trading_day'
    text = Path('src/bot_main.py').read_text()
    assert text.index('market_eligibility_source.tick(db_manager)') < text.index('target=kiwoom_sniper_v2.run_sniper')
    assert text.count('market_eligibility_source.tick(db_manager)') == 2
    assert 'update_kospi' not in Path(source.__file__).read_text()


@pytest.mark.parametrize("krx,observed_delta,expected", [
    (True,0,True),(False,0,False),(None,0,False),(True,1,False),(True,-24,False),
])
def test_current_krx_source_reaches_sor_consumer_without_nxt_inference(
    monkeypatch,krx,observed_delta,expected):
    from src.engine import sniper_state_handlers as handlers
    from src.trading.market import session_contract as contract
    now=datetime(2026,10,19,17,0,tzinfo=source.KST)
    row=dict(stock_code="036930",trade_date=now.date().isoformat(),
        source_api_id="verified-krx-source-fixture",source_revision="a"*40,
        payload_sha256="b"*64,observed_at_kst=(now+timedelta(hours=observed_delta)).isoformat(),
        krx_regular_eligible=True,krx_aftermarket_eligible=krx,nxt_eligible=False,
        quality_state="VALID",market_code="10")
    # Match the PostgreSQL aware-datetime boundary, as in the existing NXT
    # consumer proof. SQLite intentionally cannot preserve this TZ contract.
    records = {}
    def merge(model):
        records[model.stock_code] = {
            column.name: getattr(model,column.name) for column in model.__table__.columns}
    source.store_market_eligibility_rows(SimpleNamespace(merge=merge),
        trade_date=now.date(),source_rows={"036930":row})
    db=SimpleNamespace(get_security_market_eligibility=lambda code,day:records.get(code))
    monkeypatch.setattr(handlers,"DB",db)
    evidence=handlers._entry_order_venue_eligibility("036930",now=now)
    result=contract.resolve_order_type_preflight(contract.resolve_market_session(now),
        "SOR","buy","00",eligibility=evidence)
    assert result.allowed is expected
    original=db.get_security_market_eligibility("036930",now.date())
    assert original["nxt_eligible"] is False
    assert original["krx_aftermarket_eligible"] is krx
    if expected:
        assert evidence.source_id == row["source_api_id"]
        assert evidence.source_sha256 == row["payload_sha256"]


@pytest.mark.parametrize('partial', [False, True])
def test_removed_master_symbols_are_raw_evidence_without_new_master_rows(monkeypatch, db, tmp_path, partial):
    removed = source.REMOVED_MASTER_SYMBOLS
    install_pages(monkeypatch, rows={'0':[item(c) for c in sorted(removed)]+[item('005930')],
                                     '10':[item('036930')]})
    fetch = K.fetch_kiwoom_api_continuous
    if partial:
        def incomplete(**kwargs):
            responses, meta = fetch(**kwargs)
            if kwargs['payload']['mrkt_tp']=='10': meta['last_http_status_code']=500
            return responses, meta
        monkeypatch.setattr(K, 'fetch_kiwoom_api_continuous', incomplete)
    owner = runtime(tmp_path)
    result = owner.tick(db)
    assert result['status'] == ('partial' if partial else 'pass')
    assert result['stored_count'] == 2
    assert result['operator_removed_master_codes'] == sorted(removed)
    assert set(result['source_rows']) == removed|{'005930','036930'}
    day = date.fromisoformat(result['target_date'])
    for code in removed:
        assert db.get_security_market_eligibility(code,day) is None
        assert source.master_symbol_removed('A'+code+'_AL')
    assert not source.master_symbol_removed('005930')
    assert db.get_security_market_eligibility('005930',day)['quality_state'] == ('UNKNOWN' if partial else 'VALID')
    receipt = json.loads(next((tmp_path/'receipts').glob('*/latest.json')).read_text())
    assert receipt['source_rows'] == result['source_rows']
