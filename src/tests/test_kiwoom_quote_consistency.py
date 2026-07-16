from __future__ import annotations

from src.utils import kiwoom_utils


def test_ka10004_orderbook_does_not_publish_best_ask_as_curr(monkeypatch):
    def fake_fetch_kiwoom_api_continuous(**_kwargs):
        return [
            {
                "bid_req_base_tm": "093001",
                "sel_fpr_bid": "10100",
                "sel_fpr_req": "120",
                "buy_fpr_bid": "10000",
                "buy_fpr_req": "240",
                "tot_sel_req": "1000",
                "tot_buy_req": "2000",
            }
        ]

    monkeypatch.setattr(
        kiwoom_utils, "fetch_kiwoom_api_continuous", fake_fetch_kiwoom_api_continuous
    )
    snapshot = kiwoom_utils.get_stock_orderbook_ka10004("token", "005930")

    assert snapshot["curr"] == 0
    assert snapshot["rest_current_price"] == 0
    assert snapshot["best_ask"] == 10100
    assert snapshot["best_bid"] == 10000
    assert snapshot["rest_mid_price"] == 10050
    assert snapshot["marketable_buy_touch_price"] == 10100
    assert snapshot["marketable_sell_touch_price"] == 10000
    assert snapshot["passive_buy_price"] == 10000
    assert snapshot["passive_sell_price"] == 10100
    assert snapshot["executable_buy_price"] == 10100
    assert snapshot["executable_sell_price"] == 10000
    assert snapshot["bid_req_base_tm"] == "093001"
    assert snapshot["bid_req_base_tm_authority"] == "raw_not_freshness_input"
    assert snapshot["source_time_basis"] == "response_received_epoch_ms"
    assert snapshot["rest_freshness_basis"] == "response_received_epoch_ms"
    assert snapshot["rest_age_source"] == "response_received_epoch_ms"
    assert snapshot["rest_age_ms"] == 0
    assert snapshot["age_ms"] == 0
    assert snapshot["rest_received_ts_ms"] > 0


def test_ka10004_preserves_explicit_nxt_market_suffix(monkeypatch):
    calls = []

    def fake_fetch_kiwoom_api_continuous(**kwargs):
        calls.append(kwargs)
        return [
            {
                "bid_req_base_tm": "093001",
                "sel_fpr_bid": "10100",
                "sel_fpr_req": "120",
                "buy_fpr_bid": "10000",
                "buy_fpr_req": "240",
            }
        ]

    monkeypatch.setattr(
        kiwoom_utils, "fetch_kiwoom_api_continuous", fake_fetch_kiwoom_api_continuous
    )

    snapshot = kiwoom_utils.get_stock_orderbook_ka10004("token", "005930_NX")

    assert calls[0]["payload"]["stk_cd"] == "005930_NX"
    assert snapshot["stock_code"] == "005930"
    assert snapshot["request_code"] == "005930_NX"


def test_effective_kiwoom_code_preserves_explicit_market_suffix():
    assert kiwoom_utils.normalize_stock_code("A005930_NX") == "005930"
    assert (
        kiwoom_utils.get_effective_kiwoom_code("A005930_NX", is_nxt=False)
        == "005930_NX"
    )
    assert (
        kiwoom_utils.get_effective_kiwoom_code("005930_AL", is_nxt=False) == "005930_AL"
    )
