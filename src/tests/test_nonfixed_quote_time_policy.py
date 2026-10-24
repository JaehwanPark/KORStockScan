from dataclasses import FrozenInstanceError, replace
from types import SimpleNamespace

import pytest

from src.engine import sniper_entry_latency as latency
from src.engine import sniper_state_handlers as handlers
from src.trading.entry.quote_time_policy import QuoteTimePolicy, active_contract_receipt


@pytest.mark.parametrize("seconds", [1.0, 3.0, 5.0])
def test_prefixed_pre_ai_setting_controls_backoff_and_input_owner(monkeypatch, seconds):
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_AI_MAX_WS_AGE_SEC", str(seconds))
    monkeypatch.setenv("SCALP_PRE_AI_MAX_WS_AGE_SEC", "99")
    monkeypatch.setattr(handlers.time, "time", lambda: 100.0)
    assert handlers._pre_ai_quote_max_age_sec() == seconds
    assert handlers._scanner_ws_stale_backoff_recovered(
        {"curr": 100, "last_ws_update_ts": 100.0 - seconds + 0.01}
    )
    assert not handlers._scanner_ws_stale_backoff_recovered(
        {"curr": 100, "last_ws_update_ts": 100.0 - seconds - 0.01}
    )
    assert handlers._entry_quote_time_policy().budget_for("pre_ai") == seconds * 1000


def test_pre_ai_owner_uses_config_without_env_and_rejects_future_clock(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_SCALP_PRE_AI_MAX_WS_AGE_SEC", raising=False)
    monkeypatch.setattr(
        handlers, "TRADING_RULES", SimpleNamespace(SCALP_PRE_AI_MAX_WS_AGE_SEC=5.0)
    )
    monkeypatch.setattr(handlers.time, "time", lambda: 100.0)
    assert handlers._pre_ai_quote_max_age_sec() == 5.0
    assert not handlers._scanner_ws_stale_backoff_recovered(
        {"curr": 100, "last_ws_update_ts": 101.0}
    )


@pytest.mark.parametrize(
    "value,expected", [("nan", 3.0), ("inf", 3.0), ("garbage", 3.0), ("0", 0.1)]
)
def test_pre_ai_config_invalid_values_and_clamp_are_shared(
    monkeypatch, value, expected
):
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_AI_MAX_WS_AGE_SEC", value)
    assert handlers._pre_ai_quote_max_age_sec() == expected
    assert handlers._entry_quote_time_policy().budget_for("pre_ai") == expected * 1000


def test_receipt_reports_actual_owners_and_flags_without_collapsing_their_clocks(
    monkeypatch,
):
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_AI_MAX_WS_AGE_SEC", "5")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_AGE_MS", "1000")
    monkeypatch.setenv("KORSTOCKSCAN_QUOTE_CONSISTENCY_RUNTIME_ENABLED", "false")
    monkeypatch.setenv("KORSTOCKSCAN_QUOTE_CONSISTENCY_MAX_WS_AGE_MS", "600")
    monkeypatch.setattr(
        latency, "_CONFIG", replace(latency._CONFIG, max_ws_age_ms_for_caution=900)
    )
    receipt = handlers._entry_quote_time_policy()
    assert receipt.to_dict() == latency.resolved_quote_time_policy().to_dict()
    assert receipt.budget_for("pre_ai") == 5000
    assert receipt.budget_for("canonical_input") == 3000
    assert receipt.budget_for("latency") == 900
    assert receipt.budget_for("refresh") == 1000
    assert receipt.budget_for("submit_transport") == 2000
    assert receipt.consistency_enabled is False
    assert receipt.consistency_ws_max_age_ms == 600
    assert receipt.to_dict()["source_clock"] != receipt.to_dict()["transport_clock"]
    assert (
        receipt.to_dict()["sha256"]
        == latency.resolved_quote_time_policy().to_dict()["sha256"]
    )


def test_receipt_is_immutable_and_has_no_embedded_frame_authority():
    receipt = QuoteTimePolicy()
    with pytest.raises(FrozenInstanceError):
        receipt.pre_ai_max_age_ms = 9999
    with pytest.raises(ValueError):
        receipt.budget_for("unregistered_stage")
    with pytest.raises(ValueError):
        QuoteTimePolicy(refresh_max_age_ms=float("nan"))
    with pytest.raises(ValueError):
        QuoteTimePolicy(refresh_enabled="true")
    assert (
        QuoteTimePolicy(latency_caution_ms=700).to_dict()
        == QuoteTimePolicy(latency_caution_ms=700.0).to_dict()
    )


def test_disabled_diagnostic_limit_has_no_execution_authority_but_activation_does():
    policy = QuoteTimePolicy(consistency_enabled=False, refresh_enabled=False)
    changed = replace(policy, consistency_ws_max_age_ms=1, refresh_max_age_ms=1)
    assert policy.to_dict() != changed.to_dict()
    assert policy.active_contract_dict() == changed.active_contract_dict()
    assert (
        policy.active_contract_dict()
        != replace(policy, consistency_enabled=True).active_contract_dict()
    )
    assert (
        policy.active_contract_dict()
        != replace(policy, refresh_enabled=True).active_contract_dict()
    )
    broken = dict(policy.to_dict(), latency_caution_ms=9999)
    with pytest.raises(ValueError):
        active_contract_receipt(broken)


def test_verified_native_quote_uses_same_owner_for_nonfixed_and_fixed(monkeypatch):
    monkeypatch.setattr(handlers.time, "time", lambda: 100.0)
    monkeypatch.setattr(
        handlers, "_update_ai_quote_freshness_fields", lambda frame: frame
    )
    frame = {"curr": 100, "last_ws_update_ts": 97.5, "market_data_transport_epoch": 7}
    source = dict(
        source_type="0D",
        item="123456_AL",
        transport_epoch=7,
        market_route="krx_nxt_integrated",
        observed_epoch=99.9,
    )
    monkeypatch.setattr(
        handlers, "ws_quote_source_receipt", lambda data, now_ts: source
    )
    claim = {
        "snapshot": [{"source_item": "123456_AL", "native_epoch": 7, "venue": "SOR"}]
    }
    assert not handlers._scanner_async_quote_is_fresh(frame, now_ts=100)
    assert handlers._scanner_async_quote_is_fresh(
        frame, now_ts=100, validated_native_claim=claim
    )
    assert handlers._scanner_async_quote_is_fresh(
        frame, now_ts=100, native_fixed_watch=True
    )
    source["transport_epoch"] = 8
    assert not handlers._scanner_async_quote_is_fresh(
        frame, now_ts=100, validated_native_claim=claim
    )
    source["transport_epoch"] = 7
    source["market_route"] = "nxt_only"
    assert not handlers._scanner_async_quote_is_fresh(
        frame, now_ts=100, validated_native_claim=claim
    )
    source["market_route"] = "krx_nxt_integrated"
    frame["quote_stale"] = True
    assert not handlers._scanner_async_quote_is_fresh(
        frame, now_ts=100, validated_native_claim=claim
    )


@pytest.mark.parametrize("refresh_env,expected", [("700.9", 700), ("garbage", 900)])
def test_receipt_uses_actual_refresh_integer_and_invalid_env_fallback(
    monkeypatch, refresh_env, expected
):
    monkeypatch.setattr(
        handlers,
        "TRADING_RULES",
        SimpleNamespace(
            SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_AGE_MS=900, SCALP_PRE_AI_MAX_WS_AGE_SEC=5
        ),
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_AGE_MS", refresh_env
    )
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_AI_MAX_WS_AGE_SEC", "garbage")
    assert handlers._quote_refresh_max_age_ms() == expected
    assert (
        handlers._entry_quote_time_policy().to_dict()
        == latency.resolved_quote_time_policy().to_dict()
    )
    assert handlers._entry_quote_time_policy().budget_for("pre_ai") == 5000
    assert handlers._entry_quote_time_policy().budget_for("refresh") == expected
