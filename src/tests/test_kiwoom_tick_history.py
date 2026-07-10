from src.utils import kiwoom_utils


def test_get_tick_history_ka10003_marks_price_change_heuristic(monkeypatch):
    with kiwoom_utils._MARKET_DATA_CACHE_LOCK:
        kiwoom_utils._MARKET_DATA_CACHE.clear()
    monkeypatch.setattr(kiwoom_utils, "get_effective_kiwoom_code", lambda code: code)
    monkeypatch.setattr(kiwoom_utils, "get_api_url", lambda path: f"https://example.test{path}")
    monkeypatch.setattr(
        kiwoom_utils,
        "fetch_kiwoom_api_continuous",
        lambda **_kwargs: [
            {
                "cntr_infr": [
                    {
                        "tm": "090010",
                        "cur_prc": "+10110",
                        "cntr_trde_qty": "120",
                        "pre_rt": "+1.2",
                        "cntr_str": "135.5",
                        "acc_trde_qty": "1000",
                    },
                    {
                        "tm": "090009",
                        "cur_prc": "+10100",
                        "cntr_trde_qty": "50",
                        "pre_rt": "+1.1",
                        "cntr_str": "131.0",
                        "acc_trde_qty": "880",
                    },
                ]
            }
        ],
    )

    ticks = kiwoom_utils.get_tick_history_ka10003("token", "005930", limit=2)

    assert ticks[0]["dir"] == "BUY"
    assert ticks[0]["aggressor_side"] == "BUY"
    assert ticks[0]["aggressor_source"] == "price_change_heuristic"
    assert ticks[0]["aggressor_quality"] == "price_up_vs_previous_print"
    assert ticks[1]["aggressor_quality"] == "same_price_or_oldest_tick"


def test_summarize_ticks_for_realtime_ka10003_excludes_price_change_heuristic(monkeypatch):
    monkeypatch.setattr(
        kiwoom_utils,
        "get_tick_history_ka10003",
        lambda *_args, **_kwargs: [
            {
                "time": "090010",
                "price": 10110,
                "volume": 120,
                "dir": "BUY",
                "aggressor_side": "BUY",
                "aggressor_source": "price_change_heuristic",
            },
            {
                "time": "090009",
                "price": 10100,
                "volume": 80,
                "dir": "SELL",
                "aggressor_side": "SELL",
                "aggressor_source": "price_change_heuristic",
            },
        ],
    )

    summary = kiwoom_utils.summarize_ticks_for_realtime_ka10003("token", "005930", limit=2)

    assert summary["buy_exec_qty"] == 0
    assert summary["sell_exec_qty"] == 0
    assert summary["buy_ratio_now"] == 0.0
    assert summary["trade_qty_signed_now"] == 0
    assert summary["price_change_heuristic_tick_count"] == 2
    assert summary["aggressor_source_counts"] == {"price_change_heuristic": 2}


def test_get_recent_signed_trades_ka10084_preserves_signed_quantities(monkeypatch):
    with kiwoom_utils._MARKET_DATA_CACHE_LOCK:
        kiwoom_utils._MARKET_DATA_CACHE.clear()
    monkeypatch.setattr(kiwoom_utils, "get_effective_kiwoom_code", lambda code: code)
    monkeypatch.setattr(kiwoom_utils, "get_api_url", lambda path: f"https://example.test{path}")

    captured = {}

    def _fetch(**kwargs):
        captured.update(kwargs)
        return [
            {
                "tdy_pred_cntr": [
                    {
                        "tm": "151231",
                        "cur_prc": "+7320",
                        "cntr_trde_qty": "-120",
                        "cntr_str": "88.1",
                        "acc_trde_qty": "1000",
                    },
                    {
                        "tm": "151230",
                        "cur_prc": "+7330",
                        "cntr_trde_qty": "+30",
                        "cntr_str": "92.0",
                        "acc_trde_qty": "880",
                    },
                ]
            }
        ]

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", _fetch)

    ticks = kiwoom_utils.get_recent_signed_trades_ka10084("token", "005930", limit=2, tm="1512")

    assert captured["api_id"] == "ka10084"
    assert captured["payload"]["tdy_pred"] == "1"
    assert captured["payload"]["tic_min"] == "0"
    assert captured["payload"]["tm"] == "1512"
    assert ticks[0]["aggressor_side"] == "SELL"
    assert ticks[0]["signed_trade_volume"] == "-120"
    assert ticks[0]["aggressor_source"] == "kiwoom_rest_ka10084_signed_trade_qty"
    assert ticks[0]["aggressor_aux_pressure_usable"] is False
    assert ticks[1]["aggressor_side"] == "BUY"
