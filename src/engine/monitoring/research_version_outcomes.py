"""Native episode version outcomes with exact-cost, unique-owner reconciliation.

The existing ka10073 adapter owns protocol and rate limits. Publication never
queries an account. This postclose producer performs only optional read-only
cost recovery; ambiguity/partial inventory/missing costs stay null.
"""

from __future__ import annotations
from collections import defaultdict
from pathlib import Path
from src.engine.monitoring import research_closed_loop as loop
from src.engine.monitoring.low_price_two_leg_tuning import (
    _apply_broker_realized_economics,
)
from src.engine.monitoring.policy_research_economics import aware, numeric










def episode_feedback(source_date, *, report_root=None):
    from src.utils.constants import DATA_DIR

    root = Path(report_root or DATA_DIR / "report")
    path = (
        root
        / "low_price_two_leg_tuning"
        / f"low_price_two_leg_tuning_{source_date}.json"
    )
    try:
        value = loop.read_object(path, limit=128 * 1024 * 1024)
    except FileNotFoundError:
        return dict(
            status="waiting",
            reason="native_episode_version_report_missing",
            **loop.AUTHORITY,
        )
    economics = value.get("policy_version_economics")
    if (
        value.get("target_date") != str(source_date)
        or not isinstance(economics, dict)
        or economics.get("economic_basis")
        != "actual_exact_cost_completed_only_CF_separate"
    ):
        return dict(
            status="source_gap",
            reason="native_episode_version_report_invalid",
            **loop.AUTHORITY,
        )
    return dict(
        status="complete",
        source_date=str(source_date),
        source_report_sha256=loop.digest(value),
        cumulative=economics,
        rolling_last_30=value.get("policy_version_rolling_last_30"),
        holdout_last_16=value.get("policy_version_holdout_last_16"),
        **loop.AUTHORITY,
    )
