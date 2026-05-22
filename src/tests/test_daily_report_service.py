import json

from src.engine import daily_report_service as report_mod


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows


class _FakeConnection:
    def __init__(self, rows):
        self._rows = rows

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params):
        return _FakeResult(self._rows)


class _FakeEngine:
    def __init__(self, rows):
        self._rows = rows

    def connect(self):
        return _FakeConnection(self._rows)


def test_previous_day_performance_uses_completed_rows_and_net_realized_pnl(monkeypatch):
    rows = [
        {
            "rec_date": "2026-04-06",
            "stock_code": "111111",
            "stock_name": "순익반전",
            "status": "COMPLETED",
            "strategy": "SCALPING",
            "trade_type": "SCALP",
            "buy_price": 100000,
            "buy_qty": 1,
            "buy_time": "2026-04-06 09:10:00",
            "sell_price": 100100,
            "sell_time": "2026-04-06 09:12:00",
            "profit_rate": 0.1,
        },
        {
            "rec_date": "2026-04-06",
            "stock_code": "222222",
            "stock_name": "손절확정",
            "status": "COMPLETED",
            "strategy": "SCALPING",
            "trade_type": "SCALP",
            "buy_price": 10000,
            "buy_qty": 1,
            "buy_time": "2026-04-06 09:20:00",
            "sell_price": 9900,
            "sell_time": "2026-04-06 09:25:00",
            "profit_rate": -1.0,
        },
        {
            "rec_date": "2026-04-06",
            "stock_code": "333333",
            "stock_name": "잡음행",
            "status": "EXPIRED",
            "strategy": "SCALPING",
            "trade_type": "SCALP",
            "buy_price": 0,
            "buy_qty": 10,
            "buy_time": "2026-04-06 09:30:00",
            "sell_price": 50000,
            "sell_time": "2026-04-06 09:35:00",
            "profit_rate": 5.0,
        },
    ]

    monkeypatch.setattr(report_mod, "_resolve_previous_trade_date", lambda target_date, ctx: "2026-04-06")
    monkeypatch.setattr(report_mod, "_import_sqlalchemy", lambda: (None, lambda sql: sql))
    monkeypatch.setattr(report_mod, "_get_engine", lambda: _FakeEngine(rows))

    performance = report_mod._build_previous_day_performance("2026-04-07", report_mod._ReportContext(warnings=[]))

    assert performance["summary"]["completed_records"] == 2
    assert performance["summary"]["win_rate"] == 50.0
    assert performance["summary"]["avg_profit_rate"] == -0.45
    assert performance["summary"]["realized_pnl_krw"] == -253
    assert [item["code"] for item in performance["top_winners"]] == ["111111", "222222"]
    assert all(item["status"] == "COMPLETED" for item in performance["top_winners"])


def test_load_saved_daily_report_rejects_old_schema(tmp_path, monkeypatch):
    monkeypatch.setattr(report_mod, "report_path_for_date", lambda target_date: tmp_path / f"report_{target_date}.json")

    legacy_path = report_mod.report_path_for_date("2026-04-07")
    legacy_path.write_text(json.dumps({"date": "2026-04-07", "meta": {}}), encoding="utf-8")
    assert report_mod.load_saved_daily_report("2026-04-07") is None

    current_payload = {
        "date": "2026-04-07",
        "meta": {"schema_version": report_mod.REPORT_SCHEMA_VERSION},
    }
    legacy_path.write_text(json.dumps(current_payload), encoding="utf-8")
    assert report_mod.load_saved_daily_report("2026-04-07") == current_payload


def test_build_daily_report_sets_schema_version(monkeypatch):
    monkeypatch.setattr(report_mod, "_build_market_snapshot", lambda target_date, ctx: {"stocks": [], "model_ready": True})
    monkeypatch.setattr(
        report_mod,
        "_build_previous_day_performance",
        lambda target_date, ctx: {"summary": {}, "insight": "", "top_winners": [], "top_losers": [], "strategy_breakdown": []},
    )

    report = report_mod.build_daily_report("2026-04-07")

    assert report["meta"]["schema_version"] == report_mod.REPORT_SCHEMA_VERSION


def test_apply_cached_market_regime_label_uses_session_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "market_regime_snapshot.json").write_text(
        json.dumps(
            {
                "risk_state": "RISK_OFF",
                "allow_swing_entry": False,
                "swing_score": 20,
                "swing_entry_recovery_gate_score": 20,
                "market_regime_continuous_score": 41.5,
                "market_regime_continuous_label": "RISK_OFF",
                "market_regime_component_scores": {
                    "vix_level": 12.5,
                    "fear_greed_level": 8.0,
                    "domestic_breadth": 10.0,
                    "oil_relief": 7.0,
                    "local_model": 4.0,
                },
                "market_regime_score_version": "market_regime_continuous_v1",
                "market_regime_source_quality": "valid",
                "cached_session_date": "2026-04-07",
            }
        ),
        encoding="utf-8",
    )

    snapshot = {"status_text": "중립장", "status_tone": "warn"}
    report_mod._apply_cached_market_regime_label(snapshot, "2026-04-07")

    assert snapshot["status_text"] == "중립장"
    assert snapshot["status_tone"] == "warn"
    assert snapshot["risk_status_text"] == "리스크오프"
    assert snapshot["risk_status_tone"] == "bad"
    assert snapshot["regime_code"] == "BEAR"
    assert snapshot["risk_state"] == "RISK_OFF"
    assert snapshot["swing_entry_recovery_gate_score"] == 20
    assert snapshot["market_regime_continuous_score"] == 41.5
    assert snapshot["market_regime_continuous_label"] == "RISK_OFF"
    assert snapshot["market_regime_component_scores"]["domestic_breadth"] == 10.0
    assert snapshot["market_regime_score_version"] == "market_regime_continuous_v1"
    assert snapshot["market_regime_source_quality"] == "valid"
    assert snapshot["regime_source"] == "market_regime_cache"


def test_format_market_status_with_context_splits_breadth_and_continuous_regime():
    text = report_mod.format_market_status_with_context(
        {
            "status_text": "하락장",
            "ma20_ratio": 33.1,
            "market_regime_continuous_score": 64.5971,
            "market_regime_continuous_label": "NEUTRAL",
        }
    )

    assert text == "하락장(20일선 breadth 33.1%), 연속국면=NEUTRAL 64.6"
