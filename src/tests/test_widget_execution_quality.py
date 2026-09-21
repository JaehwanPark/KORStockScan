from __future__ import annotations

import json
from copy import deepcopy
from datetime import date

import pytest

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


@pytest.mark.parametrize("scoped", [True, False])
def test_operator_closure_preserves_inventory_and_is_exact_asof(tmp_path, scoped):
    failure = {
        "symbol": "005930", "execution_authority": quality.EXECUTION_OWNER,
        "event_type": "take_profit_terminal_failure",
        "observed_at": "2026-09-08T15:22:19+09:00",
        "parent_entry_signal_id": "parent", "requested_qty": 30,
    }
    if scoped:
        failure.update(execution_policy_session="KRX_REGULAR", execution_policy_id="policy")
    source = tmp_path / "widget_signal_auto_trade_events_20260908.jsonl"
    source.write_text(json.dumps(failure) + "\n")
    def load(day=21):
        return quality.load_execution_incidents(
            "005930", target_date=date(2026, 9, day), session="KRX_REGULAR",
            event_dir=tmp_path, custody_registry_path=tmp_path / "missing.jsonl")
    before = load()
    closure = {
        "symbol": "005930", "execution_authority": quality.EXECUTION_OWNER,
        "event_type": quality.OPERATOR_RESOLUTION,
        "observed_at": "2026-09-21T09:51:00+09:00",
        "authority": "explicit_operator_incident_closure_confirmation",
        "resolution_scope": "historical_order_incident_only",
        "actual_order_submitted": False, "inventory_mutation": False,
        "economics_eligible": False, "operator_confirmed_held_qty": 25,
        "operator_statement": "Historical incidents closed; Samsung 25 shares held",
        "incident_failure_sha256s": sorted(before["incidents"][0]["failure_evidence_sha256s"]),
    }
    receipt = tmp_path / "widget_signal_auto_trade_events_20260921.jsonl"
    receipt.write_text(json.dumps(closure) + "\n")
    assert load(18)["unresolved_incident_count"] == 1
    after = load()
    assert after["runtime_apply_allowed"] is True
    assert after["operator_closed_incident_count"] == 1
    assert after["resolved_incident_count"] == after["full_fill_order_count"] == 0
    assert after["incidents"][0]["operator_confirmed_held_qty"] == 25
    for key, value in [("incident_failure_sha256s", ["0" * 64]),
                       ("actual_order_submitted", True), ("economics_eligible", True),
                       ("inventory_mutation", True), ("operator_confirmed_held_qty", True),
                       ("execution_authority", "different_owner")]:
        invalid = deepcopy(closure)
        invalid[key] = value
        receipt.write_text(json.dumps(invalid) + "\n")
        assert load()["unresolved_incident_count"] == 1
    later_failure = dict(failure, observed_at="2026-09-21T10:00:00+09:00")
    receipt.write_text(json.dumps(closure) + "\n" + json.dumps(later_failure) + "\n")
    assert load()["runtime_apply_allowed"] is False
    assert load()["unresolved_incident_count"] == 1
