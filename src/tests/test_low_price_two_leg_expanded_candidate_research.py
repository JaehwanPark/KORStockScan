from __future__ import annotations

from datetime import date, timedelta

import pytest

from src.engine.monitoring import (
    low_price_two_leg_expanded_candidate_research as expanded,
)
from src.engine.monitoring.low_price_two_leg_entry_spot_research import (
    ResearchError,
    fetch_sor_history,
)
from src.trading.low_price_two_leg.profiles import PROFILES


class FakeResponse:
    status_code = 200
    headers = {}

    def __init__(self, rows):
        self._rows = rows

    def json(self):
        return {"return_code": 0, "stk_min_pole_chart_qry": self._rows}


def test_expanded_profiles_are_research_only_and_disjoint_from_live_symbols():
    assert len(expanded.RESEARCH_PROFILES) == 18
    assert set(expanded.CANDIDATE_SYMBOLS).isdisjoint(
        profile.symbol for profile in PROFILES.values()
    )
    assert {
        (profile.symbol, profile.session)
        for profile in expanded.RESEARCH_PROFILES.values()
    } == {
        (symbol, session)
        for symbol in expanded.CANDIDATE_SYMBOLS
        for session in ("midday", "afternoon")
    }


def test_fetch_expanded_symbol_requires_explicit_research_allowlist():
    started = date(2026, 6, 5)
    dates = [started + timedelta(days=index) for index in range(46)]
    rows = [
        {
            "cntr_tm": f"{item.strftime('%Y%m%d')}131500",
            "open_pric": "20000",
            "high_pric": "20100",
            "low_pric": "19900",
            "cur_prc": "20000",
        }
        for item in dates
    ]
    rows.append(
        {
            "cntr_tm": "20260604131500",
            "open_pric": "20000",
            "high_pric": "20100",
            "low_pric": "19900",
            "cur_prc": "20000",
        }
    )

    with pytest.raises(ValueError, match="symbol_not_in_selected_profile_allowlist"):
        fetch_sor_history(
            symbol="015760",
            token="TOKEN",
            start_date=started,
            end_date=dates[-1],
            post=lambda *args, **kwargs: FakeResponse(rows),
        )

    bars, meta = fetch_sor_history(
        symbol="015760",
        token="TOKEN",
        start_date=started,
        end_date=dates[-1],
        post=lambda *args, **kwargs: FakeResponse(rows),
        allowed_symbols=frozenset({"015760"}),
    )
    assert len(bars) == 46
    assert meta["source_quality_status"] == "PASS"


def test_expanded_report_fails_closed_on_incomplete_source_universe():
    with pytest.raises(ResearchError, match="expanded_candidate_source_set_mismatch"):
        expanded.build_report(
            sources={},
            start_date=expanded.CLEAN_BASELINE_DATE,
            end_date=expanded.DEFAULT_END_DATE,
        )
