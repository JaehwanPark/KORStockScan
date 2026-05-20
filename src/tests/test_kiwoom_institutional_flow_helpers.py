from src.utils import kiwoom_utils as mod


def test_ka10061_period_total_parsing(monkeypatch):
    monkeypatch.setattr(mod, "_cache_get", lambda namespace, key: None)
    monkeypatch.setattr(mod, "_cache_set", lambda namespace, key, value, ttl_sec: value)
    monkeypatch.setattr(mod, "get_effective_kiwoom_code", lambda code, is_nxt=None: code)
    monkeypatch.setattr(mod, "get_api_url", lambda path: f"https://kiwoom.test{path}")

    def fake_fetch(url, token, api_id, payload, use_continuous=False, **kwargs):
        assert api_id == "ka10061"
        assert payload["strt_dt"] == "20260514"
        return [
            {
                "stk_invsr_orgn_tot": [
                    {
                        "frgnr_invsr": "+1,000",
                        "orgn": "200",
                        "ind_invsr": "-300",
                        "fnnc_invt": "10",
                        "invtrt": "20",
                        "penfnd_etc": "30",
                        "samo_fund": "40",
                    }
                ]
            }
        ]

    monkeypatch.setattr(mod, "fetch_kiwoom_api_continuous", fake_fetch)

    result = mod.get_investor_period_total_ka10061("TOKEN", "005930", "2026-05-14", "2026-05-20")

    assert result["row_count"] == 1
    assert result["foreign_net"] == 1000
    assert result["inst_net"] == 200
    assert result["smart_money_net"] == 1200


def test_ka10064_intraday_chart_parsing(monkeypatch):
    monkeypatch.setattr(mod, "_cache_get", lambda namespace, key: None)
    monkeypatch.setattr(mod, "_cache_set", lambda namespace, key, value, ttl_sec: value)
    monkeypatch.setattr(mod, "get_effective_kiwoom_code", lambda code, is_nxt=None: code)
    monkeypatch.setattr(mod, "get_api_url", lambda path: f"https://kiwoom.test{path}")

    def fake_fetch(url, token, api_id, payload, use_continuous=False, **kwargs):
        assert api_id == "ka10064"
        return [
            {
                "opmr_invsr_trde_chart": [
                    {"tm": "090000", "frgnr_invsr": "1", "orgn": "2"},
                    {"tm": "091000", "frgnr_invsr": "3", "orgn": "4"},
                ]
            }
        ]

    monkeypatch.setattr(mod, "fetch_kiwoom_api_continuous", fake_fetch)

    result = mod.get_intraday_investor_chart_ka10064("TOKEN", "005930")

    assert result["row_count"] == 2
    assert result["latest_time"] == "091000"
    assert result["foreign_net"] == 3
    assert result["inst_net"] == 4


def test_ka10063_intraday_trade_parsing(monkeypatch):
    monkeypatch.setattr(mod, "_cache_get", lambda namespace, key: None)
    monkeypatch.setattr(mod, "_cache_set", lambda namespace, key, value, ttl_sec: value)
    monkeypatch.setattr(mod, "get_api_url", lambda path: f"https://kiwoom.test{path}")

    def fake_fetch(url, token, api_id, payload, use_continuous=False, **kwargs):
        assert api_id == "ka10063"
        return [{"opmr_invsr_trde": [{"stk_cd": "A005930", "netprps_qty": "+10", "netprps_amt": "1000"}]}]

    monkeypatch.setattr(mod, "fetch_kiwoom_api_continuous", fake_fetch)

    result = mod.get_intraday_investor_trade_ka10063("TOKEN")

    assert result["005930"]["net_qty"] == 10
    assert result["005930"]["net_amt"] == 1000


def test_ka10066_postclose_trade_parsing(monkeypatch):
    monkeypatch.setattr(mod, "_cache_get", lambda namespace, key: None)
    monkeypatch.setattr(mod, "_cache_set", lambda namespace, key, value, ttl_sec: value)
    monkeypatch.setattr(mod, "get_api_url", lambda path: f"https://kiwoom.test{path}")

    def fake_fetch(url, token, api_id, payload, use_continuous=False, **kwargs):
        assert api_id == "ka10066"
        return [{"opaf_invsr_trde": [{"stk_cd": "005930", "frgnr_invsr": "5", "orgn": "7"}]}]

    monkeypatch.setattr(mod, "fetch_kiwoom_api_continuous", fake_fetch)

    result = mod.get_postclose_investor_trade_ka10066("TOKEN")

    assert result["005930"]["foreign_net"] == 5
    assert result["005930"]["inst_net"] == 7
    assert result["005930"]["smart_money_net"] == 12
