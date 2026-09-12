from __future__ import annotations

import json
from datetime import date

from src.engine.monitoring import widget_execution_quality as quality


def test_integrated_aftermarket_preserves_route_and_unknown_actual_venue():
    row = {
        "market_data_route": "krx_nxt_integrated",
        "actual_execution_venue": "UNKNOWN",
    }

    assert quality.event_session(row) == "KRX_NXT_AFTERMARKET"


def test_integrated_aftermarket_incident_is_observe_only_runtime_veto(tmp_path):
    event = {
        "symbol": "005930",
        "execution_authority": quality.EXECUTION_OWNER,
        "event_type": "order_submit_failed",
        "observed_at": "2026-09-14T16:01:00+09:00",
        "execution_policy_session": "KRX_NXT_AFTERMARKET",
        "market_data_route": "krx_nxt_integrated",
        "actual_execution_venue": "UNKNOWN",
        "execution_policy_id": "policy-1",
        "parent_entry_signal_id": "signal-1",
        "side": "BUY",
        "ambiguous": False,
        "actual_order_submitted": False,
        "return_code": "-1",
    }
    (tmp_path / "widget_signal_auto_trade_events_20260914.jsonl").write_text(
        json.dumps(event) + "\n", encoding="utf-8"
    )

    result = quality.load_execution_incidents(
        "005930", target_date=date(2026, 9, 14), event_dir=tmp_path
    )

    assert result["dual_aftermarket_observe_only_count"] == 1
    assert result["runtime_apply_allowed"] is False
    assert result["incidents"][0]["actual_execution_venue"] == "UNKNOWN"
