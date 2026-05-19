"""Idempotent schema setup for swing strategy discovery sim.

The discovery tables are sim-only storage. They must not be consumed as broker
execution quality or real-order approval evidence.
"""

from __future__ import annotations

import argparse
from typing import Any

from sqlalchemy import create_engine, text

from src.database.models import (
    Base,
    SwingStrategyDiscoveryArm,
    SwingStrategyDiscoveryCandidate,
    SwingStrategyDiscoveryLabel,
)
from src.utils.constants import POSTGRES_URL


DISCOVERY_TABLES = (
    SwingStrategyDiscoveryCandidate.__table__,
    SwingStrategyDiscoveryArm.__table__,
    SwingStrategyDiscoveryLabel.__table__,
)


def ensure_swing_strategy_discovery_schema(db_url: str = POSTGRES_URL) -> dict[str, Any]:
    """Create discovery sim tables and indexes when missing.

    The function is intentionally safe to rerun from preopen/postclose jobs.
    """
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine, tables=list(DISCOVERY_TABLES))

    # PostgreSQL already gets the model indexes from metadata. These IF NOT
    # EXISTS statements protect databases that were created before the ORM
    # model gained an index or unique name.
    if engine.dialect.name == "postgresql":
        statements = [
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_ssd_candidate_date_code_policy ON swing_strategy_discovery_candidates (source_date, stock_code, policy_version);",
            "CREATE INDEX IF NOT EXISTS idx_ssd_candidate_date_arm ON swing_strategy_discovery_candidates (source_date, selection_arm);",
            "CREATE INDEX IF NOT EXISTS idx_ssd_candidate_date_score ON swing_strategy_discovery_candidates (source_date, lifecycle_exploration_score);",
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_ssd_arm_candidate_arm_policy ON swing_strategy_discovery_arms (candidate_id, arm_id, policy_version);",
            "CREATE INDEX IF NOT EXISTS idx_ssd_arm_date_status ON swing_strategy_discovery_arms (source_date, status);",
            "CREATE INDEX IF NOT EXISTS idx_ssd_arm_date_policy ON swing_strategy_discovery_arms (source_date, entry_policy, sizing_policy, exit_policy);",
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_ssd_label_arm_horizon_version ON swing_strategy_discovery_labels (arm_row_id, label_horizon, label_version);",
            "CREATE INDEX IF NOT EXISTS idx_ssd_label_date_horizon ON swing_strategy_discovery_labels (source_date, label_horizon);",
            "CREATE INDEX IF NOT EXISTS idx_ssd_label_date_status ON swing_strategy_discovery_labels (source_date, label_status);",
        ]
        with engine.begin() as conn:
            for statement in statements:
                conn.execute(text(statement))

    return {
        "schema_version": 1,
        "db_dialect": engine.dialect.name,
        "tables": [table.name for table in DISCOVERY_TABLES],
        "runtime_effect": False,
        "decision_authority": "swing_sim_exploration_only",
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-url", default=POSTGRES_URL)
    args = parser.parse_args(argv)
    summary = ensure_swing_strategy_discovery_schema(args.db_url)
    print(summary)


if __name__ == "__main__":
    main()
