from types import SimpleNamespace

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
