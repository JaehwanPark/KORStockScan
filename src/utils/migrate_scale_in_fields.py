"""One-off migration helper for scale-in related schema changes."""

import sys
from pathlib import Path

from sqlalchemy import create_engine, text

# Support both:
# - python -m src.utils.migrate_scale_in_fields
# - python src/utils/migrate_scale_in_fields.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.utils.constants import POSTGRES_URL


DDL_STATEMENTS = [
    "ALTER TABLE recommendation_history ADD COLUMN IF NOT EXISTS add_count INTEGER DEFAULT 0;",
    "ALTER TABLE recommendation_history ADD COLUMN IF NOT EXISTS avg_down_count INTEGER DEFAULT 0;",
    "ALTER TABLE recommendation_history ADD COLUMN IF NOT EXISTS pyramid_count INTEGER DEFAULT 0;",
    "ALTER TABLE recommendation_history ADD COLUMN IF NOT EXISTS last_add_type TEXT;",
    "ALTER TABLE recommendation_history ADD COLUMN IF NOT EXISTS last_add_at TIMESTAMP;",
    "ALTER TABLE recommendation_history ADD COLUMN IF NOT EXISTS scale_in_locked BOOLEAN DEFAULT false;",
    "ALTER TABLE recommendation_history ADD COLUMN IF NOT EXISTS hard_stop_price DOUBLE PRECISION;",
    "ALTER TABLE recommendation_history ADD COLUMN IF NOT EXISTS trailing_stop_price DOUBLE PRECISION;",
    (
        "ALTER TABLE recommendation_history "
        "ALTER COLUMN buy_price TYPE DOUBLE PRECISION USING buy_price::double precision;"
    ),
    """
    CREATE TABLE IF NOT EXISTS holding_add_history (
        id SERIAL PRIMARY KEY,
        recommendation_id INTEGER NOT NULL,
        stock_code VARCHAR(10) NOT NULL,
        stock_name TEXT,
        strategy TEXT,
        add_type TEXT,
        event_type TEXT NOT NULL,
        event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        order_no TEXT,
        request_qty INTEGER DEFAULT 0,
        executed_qty INTEGER DEFAULT 0,
        request_price DOUBLE PRECISION,
        executed_price DOUBLE PRECISION,
        prev_buy_price DOUBLE PRECISION,
        new_buy_price DOUBLE PRECISION,
        prev_buy_qty INTEGER DEFAULT 0,
        new_buy_qty INTEGER DEFAULT 0,
        add_count_after INTEGER DEFAULT 0,
        reason TEXT,
        note TEXT
    );
    """,
]


def run():
    engine = create_engine(POSTGRES_URL)
    with engine.begin() as conn:
        for stmt in DDL_STATEMENTS:
            conn.execute(text(stmt))
            print(f"[OK] {stmt}")


if __name__ == "__main__":
    run()
