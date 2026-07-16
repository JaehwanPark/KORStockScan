from types import SimpleNamespace

import pandas as pd

from src.database.db_manager import DBManager


class _FakeConnection:
    def __init__(self):
        self.statements = []

    def execution_options(self, **kwargs):
        return self

    def execute(self, statement):
        self.statements.append(str(statement))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeEngine:
    def __init__(self):
        self.dialect = SimpleNamespace(name="postgresql")
        self.connection = _FakeConnection()

    def connect(self):
        return self.connection

    def begin(self):
        return self.connection


def test_ensure_performance_table_indexes_covers_db_tuning_hot_paths():
    db = object.__new__(DBManager)
    db.engine = _FakeEngine()

    db._ensure_performance_table_indexes()

    statements = "\n".join(db.engine.connection.statements)
    assert "idx_dsq_stock_code_quote_date_desc" in statements
    assert "idx_rh_status_rec_date" in statements
    assert "idx_rh_rec_date_stock_strategy_status" in statements
    assert "idx_rh_reusable_watching_lookup" in statements


def test_analyze_performance_tables_includes_quote_and_history_tables():
    db = object.__new__(DBManager)
    db.engine = _FakeEngine()

    db.analyze_performance_tables()

    statements = "\n".join(db.engine.connection.statements)
    assert "ANALYZE daily_stock_quotes;" in statements
    assert "ANALYZE recommendation_history;" in statements
    assert "ANALYZE trade_performance_facts;" in statements


def test_save_recommendation_skips_swing_watching_by_default(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_SWING_REAL_WATCHING_ENABLED", raising=False)
    db = object.__new__(DBManager)

    def fail_get_session():
        raise AssertionError("disabled swing WATCHING should not open a DB session")

    db.get_session = fail_get_session

    assert (
        db.save_recommendation(
            date="2026-06-23",
            code="005930",
            name="Samsung",
            price=70000,
            pick_type="MAIN",
            position="META_V2",
            strategy="KOSPI_ML",
        )
        is None
    )


class _FakeSessionContext:
    def __init__(self):
        self.bind = object()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_get_active_targets_filters_only_swing_watching_by_default(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_SWING_REAL_WATCHING_ENABLED", raising=False)
    db = object.__new__(DBManager)
    db.get_session = lambda: _FakeSessionContext()

    rows = pd.DataFrame(
        [
            {
                "id": 1,
                "date": "2026-06-23",
                "code": "005930",
                "name": "Samsung",
                "type": "MAIN",
                "status": "WATCHING",
                "strategy": "KOSPI_ML",
                "position_tag": "META_V2",
                "prob": 0.7,
            },
            {
                "id": 2,
                "date": "2026-06-23",
                "code": "000660",
                "name": "SK hynix",
                "type": "MAIN",
                "status": "HOLDING",
                "strategy": "KOSPI_ML",
                "position_tag": "META_V2",
                "prob": 0.7,
            },
            {
                "id": 3,
                "date": "2026-06-23",
                "code": "123456",
                "name": "Scanner",
                "type": "SCALP",
                "status": "WATCHING",
                "strategy": "SCALPING",
                "position_tag": "SCANNER",
                "prob": 0.7,
            },
        ]
    )

    monkeypatch.setattr(pd, "read_sql", lambda query, bind: rows.copy())

    targets = db.get_active_targets()
    codes = {target["code"] for target in targets}

    assert codes == {"000660", "123456"}
