from src.utils import kiwoom_utils


def test_get_tick_history_ka10003_marks_price_change_heuristic(monkeypatch):
    with kiwoom_utils._MARKET_DATA_CACHE_LOCK:
        kiwoom_utils._MARKET_DATA_CACHE.clear()
    monkeypatch.setattr(kiwoom_utils, "get_effective_kiwoom_code", lambda code: code)
    monkeypatch.setattr(
        kiwoom_utils, "get_api_url", lambda path: f"https://example.test{path}"
    )
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
    assert ticks[0]["raw"]["cntr_trde_qty"] == "120"
    assert ticks[1]["aggressor_quality"] == "same_price_or_oldest_tick"


def test_compute_buy_dominance_from_ka10003_entries_uses_split_signed_and_quote_touch():
    stats = kiwoom_utils.compute_buy_dominance_from_ka10003_entries(
        [
            {
                "tm": "090010",
                "cur_prc": "1000",
                "1031": "30",
                "1030": "10",
                "cntr_trde_qty": "+40",
                "1313": "40000",
            },
            {"tm": "090009", "cur_prc": "1000", "cntr_trde_qty": "+20"},
            {"tm": "090008", "cur_prc": "990", "cntr_trde_qty": "-15"},
            {
                "tm": "090007",
                "cur_prc": "1000",
                "cntr_trde_qty": "12",
                "pri_sel_bid_unit": "1000",
                "pri_buy_bid_unit": "990",
            },
            {
                "tm": "090006",
                "cur_prc": "995",
                "cntr_trde_qty": "8",
                "pri_sel_bid_unit": "1000",
                "pri_buy_bid_unit": "990",
            },
        ],
        limit=10,
    )

    assert stats["runtime_effect"] is False
    assert stats["allowed_runtime_apply"] is False
    assert stats["buy_volume"] == 62.0
    assert stats["sell_volume"] == 25.0
    assert round(stats["buy_ratio"], 6) == round(62 / 87, 6)
    assert stats["source_counts"] == {
        "1030_1031_split": 1,
        "signed_volume": 2,
        "quote_touch": 1,
        "inside_excluded": 1,
    }
    assert stats["trade_value_source_counts"] == {"1313": 1, "calc_price_x_volume": 3}
    assert stats["split_vs_15_evaluable_count"] == 1
    assert stats["split_vs_15_mismatch_count"] == 0
    assert stats["inside_spread_count"] == 1


def test_compute_buy_dominance_from_ka10003_entries_can_split_inside_spread():
    stats = kiwoom_utils.compute_buy_dominance_from_ka10003_entries(
        [
            {
                "tm": "090006",
                "cur_prc": "995",
                "cntr_trde_qty": "8",
                "pri_sel_bid_unit": "1000",
                "pri_buy_bid_unit": "990",
            },
        ],
        include_inside=True,
    )

    assert stats["buy_volume"] == 4.0
    assert stats["sell_volume"] == 4.0
    assert stats["buy_dominance"] == 0.0
    assert stats["source_counts"] == {"inside_split": 1}


def test_summarize_ticks_for_realtime_ka10003_excludes_price_change_heuristic(
    monkeypatch,
):
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

    summary = kiwoom_utils.summarize_ticks_for_realtime_ka10003(
        "token", "005930", limit=2
    )

    assert summary["buy_exec_qty"] == 0
    assert summary["sell_exec_qty"] == 0
    assert summary["buy_ratio_now"] == 0.0
    assert summary["trade_qty_signed_now"] == 0
    assert summary["price_change_heuristic_tick_count"] == 2
    assert summary["aggressor_source_counts"] == {"price_change_heuristic": 2}


def test_summarize_ticks_for_realtime_ka10003_attaches_source_only_raw_observation(
    monkeypatch,
):
    monkeypatch.setattr(
        kiwoom_utils,
        "get_tick_history_ka10003",
        lambda *_args, **_kwargs: [
            {
                "time": "090010",
                "price": 1000,
                "volume": 40,
                "dir": "BUY",
                "aggressor_side": "BUY",
                "aggressor_source": "price_change_heuristic",
                "raw": {
                    "tm": "090010",
                    "cur_prc": "1000",
                    "1031": "30",
                    "1030": "10",
                    "cntr_trde_qty": "+40",
                    "1313": "40000",
                },
            }
        ],
    )

    summary = kiwoom_utils.summarize_ticks_for_realtime_ka10003(
        "token", "005930", limit=1
    )

    assert summary["buy_exec_qty"] == 0
    observation = summary["ka10003_buy_dominance_observation"]
    assert observation["decision_authority"] == "source_quality_only"
    assert observation["buy_volume"] == 30.0
    assert observation["sell_volume"] == 10.0
    assert observation["source_counts"] == {"1030_1031_split": 1}
    assert summary["ka10003_buy_dominance_observation_source_counts"] == {
        "1030_1031_split": 1
    }
    assert summary["ka10003_buy_dominance_observation_trade_value_source_counts"] == {
        "1313": 1
    }
    assert summary["ka10003_buy_dominance_observation_inside_spread_count"] == 0
    assert summary["ka10003_buy_dominance_observation_split_vs_15_evaluable_count"] == 1
    assert summary["ka10003_buy_dominance_observation_split_vs_15_mismatch_count"] == 0


def test_get_recent_signed_trades_ka10084_preserves_signed_quantities(monkeypatch):
    with kiwoom_utils._MARKET_DATA_CACHE_LOCK:
        kiwoom_utils._MARKET_DATA_CACHE.clear()
    monkeypatch.setattr(kiwoom_utils, "get_effective_kiwoom_code", lambda code: code)
    monkeypatch.setattr(
        kiwoom_utils, "get_api_url", lambda path: f"https://example.test{path}"
    )

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

    ticks = kiwoom_utils.get_recent_signed_trades_ka10084(
        "token", "005930", limit=2, tm="1512"
    )

    assert captured["api_id"] == "ka10084"
    assert captured["payload"]["tdy_pred"] == "1"
    assert captured["payload"]["tic_min"] == "0"
    assert captured["payload"]["tm"] == "1512"
    assert ticks[0]["aggressor_side"] == "SELL"
    assert ticks[0]["signed_trade_volume"] == "-120"
    assert ticks[0]["aggressor_source"] == "kiwoom_rest_ka10084_signed_trade_qty"
    assert ticks[0]["aggressor_aux_pressure_usable"] is False
    assert ticks[1]["aggressor_side"] == "BUY"
