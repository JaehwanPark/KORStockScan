import json

from src.engine import institutional_flow_context as mod


def test_normalize_institutional_flow_context_builds_source_only_features():
    context = mod.normalize_institutional_flow_context(
        "A005930",
        daily_summary={"smart_money_net": 1200},
        period_summary={"foreign_net": 500, "inst_net": 700},
        intraday_chart_qty={"foreign_net": 30, "inst_net": 40},
        intraday_chart_amt={"foreign_net": 3000, "inst_net": 4000},
        ws_data={
            "received_types": {"0F", "0w"},
            "foreign_broker_net_est_qty": 90,
            "foreign_broker_net_est_delta_qty": 10,
            "prog_net_qty": 100,
            "prog_delta_qty": 20,
            "prog_net_amt": 5000,
        },
    )

    assert context["stock_code"] == "005930"
    assert context["foreign_net_intraday_qty"] == 30
    assert context["institution_net_intraday_qty"] == 40
    assert context["dual_net_buy"] is True
    assert context["institutional_flow_regime"] == "DUAL_ACCUMULATION"
    assert context["institutional_flow_status"] == "OK"
    assert context["runtime_effect"] is False
    assert context["decision_authority"] == "source_only_lifecycle_feature"


def test_resolver_uses_kiwoom_helpers_and_handles_token_error(monkeypatch):
    called = []

    def fake_daily(token, code, base_dt=None):
        called.append(("ka10059", token, code, base_dt))
        return {"smart_money_net": 10}

    def fake_period(token, code, start_dt, end_dt):
        called.append(("ka10061", token, code, start_dt, end_dt))
        return {"foreign_net": 4, "inst_net": 6}

    monkeypatch.setattr(mod.kiwoom_utils, "get_investor_flow_summary_ka10059", fake_daily)
    monkeypatch.setattr(mod.kiwoom_utils, "get_investor_period_total_ka10061", fake_period)

    no_token = mod.resolve_institutional_flow_context("005930", token=None, target_date="2026-05-20")
    assert no_token["institutional_flow_status"] == "TOKEN_ERROR"
    assert called == []

    context = mod.resolve_institutional_flow_context("005930", token="T", target_date="2026-05-20")
    assert context["institutional_flow_status"] == "OK"
    assert context["smart_money_net"] == 10
    assert [item[0] for item in called] == ["ka10059", "ka10061"]


def test_build_report_writes_artifact(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR_PATH", tmp_path)
    monkeypatch.setattr(mod.kiwoom_utils, "get_kiwoom_token", lambda: "T")
    monkeypatch.setattr(
        mod,
        "resolve_institutional_flow_context",
        lambda code, **kwargs: {
            "stock_code": code,
            "smart_money_net": 100,
            "foreign_net_roll5": 50,
            "inst_net_roll5": 50,
            "institutional_flow_regime": "DUAL_ACCUMULATION",
            "institutional_flow_source": "ka10059+ka10061",
            "institutional_flow_status": "OK",
            "runtime_effect": False,
            "decision_authority": "source_only_lifecycle_feature",
        },
    )

    report = mod.build_institutional_flow_context_report("2026-05-20", codes=["005930", "005930", "000660"])

    assert report["summary"]["row_count"] == 2
    assert report["summary"]["ok_count"] == 2
    assert report["runtime_effect"] is False
    assert (tmp_path / "institutional_flow_context_2026-05-20.json").exists()
    payload = json.loads((tmp_path / "institutional_flow_context_2026-05-20.json").read_text(encoding="utf-8"))
    assert payload["rows"][0]["decision_authority"] == "source_only_lifecycle_feature"
