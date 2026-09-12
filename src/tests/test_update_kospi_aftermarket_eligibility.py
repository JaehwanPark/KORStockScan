from datetime import date, datetime
from zoneinfo import ZoneInfo

from src.database.db_manager import DBManager
from src.database.models import Base
from src.utils import kiwoom_utils, update_kospi


KST = ZoneInfo("Asia/Seoul")


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
