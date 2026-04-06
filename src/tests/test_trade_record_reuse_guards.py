from datetime import date

from src.database.db_manager import DBManager
from src.database.models import RecommendationHistory


class _DummyQuery:
    def __init__(self, records):
        self.records = list(records)

    def filter(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def first(self):
        reusable = []
        for record in self.records:
            if str(record.status or "") not in {"WATCHING", "EXPIRED"}:
                continue
            if getattr(record, "buy_time", None):
                continue
            if int(getattr(record, "buy_qty", 0) or 0) != 0:
                continue
            reusable.append(record)
        return reusable[-1] if reusable else None


class _DummySession:
    def __init__(self, records):
        self.records = records

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def query(self, _model):
        return _DummyQuery(self.records)

    def add(self, record):
        record.id = len(self.records) + 1
        self.records.append(record)


class _DummyDB(DBManager):
    def __init__(self):
        self.records = []

    def get_session(self):
        return _DummySession(self.records)

    def find_reusable_watching_record(self, session, *, rec_date, stock_code, strategy=None):
        for record in reversed(session.records):
            if getattr(record, "rec_date", None) != rec_date:
                continue
            if getattr(record, "stock_code", None) != stock_code:
                continue
            if strategy is not None and getattr(record, "strategy", None) != strategy:
                continue
            if str(getattr(record, "status", "") or "") not in {"WATCHING", "EXPIRED"}:
                continue
            if getattr(record, "buy_time", None):
                continue
            if int(getattr(record, "buy_qty", 0) or 0) != 0:
                continue
            return record
        return None


def test_save_recommendation_does_not_reuse_completed_trade_row():
    db = _DummyDB()
    trade_date = date(2026, 4, 6)
    completed = RecommendationHistory(
        id=1085,
        rec_date=trade_date,
        stock_code="222800",
        stock_name="심텍",
        trade_type="SCALP",
        strategy="SCALPING",
        status="COMPLETED",
        position_tag="SCANNER",
        buy_price=57000,
        buy_qty=10,
    )
    db.records.append(completed)

    db.save_recommendation(
        date=trade_date,
        code="222800",
        name="심텍",
        price=0,
        pick_type="SCALP",
        position="SCANNER",
        strategy="SCALPING",
    )

    assert len(db.records) == 2
    assert db.records[0].status == "COMPLETED"
    assert db.records[0].buy_price == 57000
    assert db.records[1].status == "WATCHING"
    assert db.records[1].buy_price == 0


def test_register_manual_stock_reuses_only_empty_watching_row():
    db = _DummyDB()
    today = date.today()
    completed = RecommendationHistory(
        id=1,
        rec_date=today,
        stock_code="005930",
        stock_name="삼성전자",
        trade_type="SCALP",
        strategy="SCALPING",
        status="COMPLETED",
        position_tag="SCANNER",
        buy_price=60000,
        buy_qty=1,
    )
    watching = RecommendationHistory(
        id=2,
        rec_date=today,
        stock_code="005930",
        stock_name="삼성전자",
        trade_type="SCALP",
        strategy="SCALPING",
        status="WATCHING",
        position_tag="SCANNER",
        buy_price=0,
        buy_qty=0,
    )
    db.records.extend([completed, watching])

    assert db.register_manual_stock("005930", "삼성전자") is True

    assert len(db.records) == 2
    assert db.records[0].status == "COMPLETED"
    assert db.records[1].status == "WATCHING"
    assert db.records[1].stock_name == "삼성전자"
