from datetime import date, datetime, timezone

from sqlalchemy import create_engine, inspect, text

from src.database.db_manager import DBManager
from src.database.models import Base, SecurityMarketEligibilityDaily


def _sqlite_db(tmp_path, name: str) -> DBManager:
    return DBManager(f"sqlite:///{tmp_path / name}")


def test_clean_database_creates_market_eligibility_schema(tmp_path):
    db = _sqlite_db(tmp_path, "clean.sqlite3")

    db.init_db()

    columns = {
        column["name"]
        for column in inspect(db.engine).get_columns(
            SecurityMarketEligibilityDaily.__tablename__
        )
    }
    assert columns == {
        "trade_date",
        "stock_code",
        "krx_regular_eligible",
        "nxt_eligible",
        "krx_aftermarket_eligible",
        "eligible_venues_json",
        "audit_info",
        "stock_state",
        "order_warning",
        "market_code",
        "source_api_id",
        "source_revision",
        "observed_at_kst",
        "payload_sha256",
        "quality_state",
        "blocked_reasons_json",
    }


def test_existing_database_gets_additive_market_eligibility_table(tmp_path):
    db = _sqlite_db(tmp_path, "existing.sqlite3")
    with db.engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE daily_stock_quotes (
                quote_date DATE NOT NULL,
                stock_code VARCHAR(10) NOT NULL,
                is_nxt BOOLEAN,
                PRIMARY KEY (quote_date, stock_code)
            )
        """))
        conn.execute(
            text("""
                INSERT INTO daily_stock_quotes (quote_date, stock_code, is_nxt)
                VALUES ('2026-09-11', '005930', true)
            """)
        )

    db.init_db()

    assert inspect(db.engine).has_table("security_market_eligibility_daily")
    with db.engine.connect() as conn:
        old_row = conn.execute(
            text("""
                SELECT quote_date, stock_code, is_nxt
                FROM daily_stock_quotes
                WHERE stock_code = '005930'
            """)
        ).first()
    assert old_row == ("2026-09-11", "005930", 1)


def test_reader_prefers_new_row_and_preserves_nullable_axes(tmp_path):
    db = _sqlite_db(tmp_path, "new-row.sqlite3")
    Base.metadata.create_all(db.engine)
    observed_at = datetime(2026, 9, 11, 16, 5, tzinfo=timezone.utc)
    with db.get_session() as session:
        session.add(
            SecurityMarketEligibilityDaily(
                trade_date=date(2026, 9, 11),
                stock_code="005930",
                krx_regular_eligible=True,
                nxt_eligible=True,
                krx_aftermarket_eligible=None,
                eligible_venues_json=["KRX", "NXT"],
                audit_info="normal",
                stock_state="active",
                order_warning="none",
                market_code="0",
                source_api_id="ka10099",
                source_revision="official-test-revision",
                observed_at_kst=observed_at,
                payload_sha256="a" * 64,
                quality_state="PARTIAL",
                blocked_reasons_json=["krx_aftermarket_eligibility_unknown"],
            )
        )

    row = db.get_security_market_eligibility("005930_AL", "2026-09-11")

    assert row is not None
    assert row["nxt_eligible"] is True
    assert row["krx_aftermarket_eligible"] is None
    assert row["eligible_venues_json"] == ["KRX", "NXT"]
    assert row["blocked_reasons_json"] == ["krx_aftermarket_eligibility_unknown"]
    assert row["source_api_id"] == "ka10099"


def test_reader_reads_old_is_nxt_row_without_aftermarket_inference(tmp_path):
    db = _sqlite_db(tmp_path, "legacy-only.sqlite3")
    with db.engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE daily_stock_quotes (
                quote_date DATE NOT NULL,
                stock_code VARCHAR(10) NOT NULL,
                is_nxt BOOLEAN,
                PRIMARY KEY (quote_date, stock_code)
            )
        """))
        conn.execute(
            text("""
                INSERT INTO daily_stock_quotes (quote_date, stock_code, is_nxt)
                VALUES ('2026-09-11', '005930', true)
            """)
        )

    row = db.get_security_market_eligibility("005930_NX", date(2026, 9, 11))

    assert row is not None
    assert row["krx_regular_eligible"] is True
    assert row["nxt_eligible"] is True
    assert row["krx_aftermarket_eligible"] is None
    assert row["quality_state"] == "PARTIAL"
    assert "krx_aftermarket_eligibility_unknown" in row["blocked_reasons_json"]
