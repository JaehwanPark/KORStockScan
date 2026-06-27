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

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", fake_fetch_kiwoom_api_continuous)
    snapshot = kiwoom_utils.get_stock_orderbook_ka10004("token", "005930")

    assert snapshot["curr"] == 0
    assert snapshot["rest_current_price"] == 0
    assert snapshot["best_ask"] == 10100
    assert snapshot["best_bid"] == 10000
    assert snapshot["rest_mid_price"] == 10050
    assert snapshot["executable_buy_price"] == 10000
    assert snapshot["executable_sell_price"] == 10000
