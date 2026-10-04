"""New producer -> canonical capture -> default public postclose loader.

Synthetic tmp fixtures only; no historical repair argument or live cache.
"""
from copy import deepcopy
from datetime import datetime, timedelta
import json

import pytest

from src.engine.scalping import ai_decision_trace as trace
from src.engine.scalping import ai_action_outcome_calibration as calibration
from src.engine.scalping import ai_decision_quality as quality
from src.engine.scalping import entry_setup_evidence as E, entry_strategy_policy as S
from src.tests.test_ai_decision_trace import _enable
from src.tests.test_entry_setup_source_repair import case
from src.tests.test_entry_strategy_policy import setup


@pytest.mark.parametrize("micro_price,large_sell", [(0, False), (.05, False), (0, True)])
@pytest.mark.parametrize("independent,economics", [(True, False), (False, False), (False, True)])
def test_new_capture_default_loader_roundtrip_and_cache(case, tmp_path, monkeypatch,
                                                      micro_price, large_sell, independent, economics):
    old, bundle, _, _ = case
    scratch = tmp_path / "default-roundtrip"
    _enable(monkeypatch, scratch)
    now = datetime.fromisoformat("2026-10-06T10:33:18.1+09:00")
    monkeypatch.setattr(trace, "_now", lambda: now)
    payload = deepcopy(old["source"]["exact_payload"])
    payload["strategy_observed_at"] = "2026-10-06T10:33:18+09:00"
    payload["features"].update(price_change_10t_pct=micro_price, large_sell_print_detected=large_sell)
    if economics:
        payload.update(best_ask=10000, conservative_execution_cost_pct=.02)
        profile = dict(profile_id="reviewed", economic_source_sha256="a" * 64,
            buy_fee_bps=1, sell_fee_bps=1, statutory_sell_tax_bps=15, uncertainty_buffer_bps=1)
        monkeypatch.setattr(calibration, "_hierarchy_cost_profiles", lambda *a: {"005930": profile})
        prices = [dict(stock_code="005930", timestamp=(now + timedelta(seconds=i * 30)).isoformat(),
            price=10050, high=10055, low=10000, close=10050, effective_venue="KRX",
            session_bucket="KRX_REGULAR", source_quality="pass", source_request_code="005930")
            for i in range(1, 21)]
        monkeypatch.setattr(quality, "load_pipeline_price_and_lifecycle_rows", lambda *a, **kw: (prices, []))
    evidence, _, _ = S.rebuild(setup(payload), bundle["machine_policy"])
    decision = E.mechanistic_entry_policy_decision(evidence, policy=bundle["machine_policy"])
    assert E.validate_entry_setup_evidence(evidence) == []
    assert decision["action"] == ("BLOCK" if large_sell else "RECHECK")
    capture = trace.capture_machine_observation(exact_payload=payload, setup_evidence=evidence,
        assessment=decision, bundle_sha256=bundle["bundle_sha256"],
        metadata={"source_event_stage": "entry_machine_only_v1"})
    assert capture["machine_capture_status"] == "captured"
    options = dict(target_date="2026-10-06", minimum_source_date="2026-10-06")
    if independent: options["independent_machine"] = True
    rows, cold = calibration.load_machine_observation_rows(scratch, **options)
    assert cold.get("invalid_capture", 0) == 0
    assert len(rows) == (1 if independent or economics else 0)
    assert "source_setup_repair_accepted" not in cold
    if rows:
        assert "source_setup_repair" not in rows[0]
        assert rows[0]["decision_trace_id"] == capture["machine_observation_sha256"]
        assert rows[0]["machine_action"] == decision["action"]
        assert rows[0]["watch_admission_id"] == payload["watch_admission_id"]
        assert rows[0]["entry_quality_contract_valid"] is economics
    else:
        assert cold["full_round_trip_cost_missing"] == 1
    monkeypatch.setattr(calibration, "_load_machine_observation_rows_uncached",
                        lambda *args, **kwargs: pytest.fail("warm projection did not reuse"))
    again, warm = calibration.load_machine_observation_rows(scratch, **options)
    assert list(again) == list(rows)
    assert warm["frozen_projection_receipts"][0]["cache_reused"] is True
    archived = json.loads((scratch / "ai_decision_payloads/ai_decision_payloads_2026-10-06.jsonl").read_text())
    assert archived["actual_order_submitted"] is False and archived["provider_called"] is False
