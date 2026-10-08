import json
from datetime import datetime

from src.market_regime.schemas import MarketRegimeSnapshot
from src.market_regime import service as service_mod


def test_cnn_adapter_preserves_fields_without_global_cache(monkeypatch):
    import requests
    import importlib
    from types import SimpleNamespace
    from src.market_regime.data_provider import CNNFearGreedProvider
    original=(requests.Session,requests.sessions.Session)
    importlib.reload(service_mod)
    assert (requests.Session,requests.sessions.Session)==original
    adapter=CNNFearGreedProvider()
    adapter._session=SimpleNamespace(get=lambda *a,**k:SimpleNamespace(
        raise_for_status=lambda:None,json=lambda:{'fear_and_greed':dict(score=64.5,rating='greed',timestamp='2026-10-08T00:00:00+00:00')}))
    v=adapter.get()
    assert (v.value,v.description,v.last_update.isoformat())==(64.5,'greed','2026-10-08T00:00:00+00:00')
    monkeypatch.setattr(service_mod,'fear_and_greed',adapter)
    service=object.__new__(service_mod.MarketRegimeService)
    service._snapshot=_snapshot()
    assert service._fetch_fear_and_greed_data()['previous_value']==40.
    adapter._session=SimpleNamespace(get=lambda *a,**k: (_ for _ in ()).throw(TimeoutError('offline')))
    fallback=service._fetch_fear_and_greed_data()
    assert fallback['source']=='cached_fallback' and fallback['value']==40.


def _snapshot(score: int = 35) -> MarketRegimeSnapshot:
    return MarketRegimeSnapshot(
        timestamp=datetime(2026, 5, 12, 8, 30),
        vix_close=22.0,
        fng_value=40.0,
        wti_from_recent_high_pct=-5.0,
        oil_reversal=True,
        oil_pullback_relief=True,
        swing_score=score,
        swing_entry_recovery_gate_score=score,
        risk_state="RISK_OFF",
        allow_swing_entry=False,
        debug={
            "score_threshold": 70,
            "component_scores": {"vix": 0, "oil": score, "fng": 0},
        },
        reasons=["원유 반전 시그널"],
    )


def test_local_breadth_overlay_can_open_swing_gate(monkeypatch, tmp_path):
    monkeypatch.setattr(service_mod, "DATA_DIR", tmp_path)
    service = service_mod.MarketRegimeService(refresh_minutes=0)

    snap = service._apply_local_market_context(
        _snapshot(),
        {
            "ma20_ratio": 62.8,
            "bull_regime": 1,
            "safe_pool_count": 61,
        },
    )

    assert snap.swing_score == 70
    assert snap.allow_swing_entry is True
    assert snap.risk_state == "RISK_ON"
    assert snap.recovery_gate_state == "READY"
    assert snap.oil_only_recovery_prior is False
    assert snap.debug["component_scores"]["local_breadth"] == 35
    assert any("국내 breadth 상승장" in reason for reason in snap.reasons)


def test_local_breadth_overlay_does_not_override_unresolved_extreme_vix(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(service_mod, "DATA_DIR", tmp_path)
    service = service_mod.MarketRegimeService(refresh_minutes=0)
    snap = _snapshot()
    snap.vix_extreme = True
    snap.vix_two_day_down = False

    snap = service._apply_local_market_context(
        snap,
        {
            "ma20_ratio": 72.0,
            "bull_regime": 1,
            "safe_pool_count": 80,
        },
    )

    assert snap.swing_score == 35
    assert snap.allow_swing_entry is False
    assert snap.risk_state == "RISK_OFF"
    assert snap.recovery_gate_state == "INSUFFICIENT"
    assert snap.recovery_gate_reason == "oil_only_recovery_signal_insufficient"
    assert snap.oil_only_recovery_prior is True
    assert snap.debug["component_scores"]["local_breadth"] == 0


def test_load_local_market_context_prefers_daily_report_and_adds_diagnostics(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(service_mod, "DATA_DIR", tmp_path)
    report_dir = tmp_path / "report"
    report_dir.mkdir(parents=True)
    (report_dir / "report_2026-05-12.json").write_text(
        json.dumps(
            {
                "stats": {
                    "quote_date": "2026-05-11",
                    "status_text": "상승장",
                    "ma20_ratio": 62.8,
                    "avg_bull": 58.2,
                    "qualified_count": 7,
                    "total_valid": 12,
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (tmp_path / "daily_recommendations_v2_diagnostics.json").write_text(
        json.dumps(
            {
                "latest_stats": {
                    "date": "2026-05-11 00:00:00",
                    "bull_regime": 1,
                    "safe_pool_count": 61,
                    "candidate_count": 296,
                    "selection_mode": "SELECTED",
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    service = service_mod.MarketRegimeService(refresh_minutes=0)
    context = service._load_local_market_context("2026-05-12")

    assert context["ma20_ratio"] == 62.8
    assert context["daily_status_text"] == "상승장"
    assert context["quote_date"] == "2026-05-11"
    assert context["avg_bull"] == 58.2
    assert context["qualified_count"] == 7
    assert context["total_valid"] == 12
    assert context["bull_regime"] == 1
    assert context["safe_pool_count"] == 61


def test_continuous_score_counts_partial_breadth_even_when_gate_score_is_zero(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(service_mod, "DATA_DIR", tmp_path)
    service = service_mod.MarketRegimeService(refresh_minutes=0)
    snap = _snapshot(score=0)
    snap.oil_reversal = False
    snap.oil_pullback_relief = False
    snap.wti_from_recent_high_pct = 0.0
    snap.debug["component_scores"] = {"vix": 0, "oil": 0, "fng": 0}

    snap = service._apply_local_market_context(
        snap,
        {
            "ma20_ratio": 20.0,
            "avg_bull": 53.0,
            "qualified_count": 3,
            "total_valid": 15,
        },
    )

    assert snap.swing_score == 0
    assert snap.swing_entry_recovery_gate_score == 0
    assert snap.market_regime_component_scores["domestic_breadth"] == 10.0
    assert snap.market_regime_component_scores["local_model"] == 4.0
    assert snap.market_regime_continuous_score > 0.0
    assert snap.market_regime_continuous_label in {"RISK_OFF", "NEUTRAL", "RISK_ON"}
    assert snap.market_regime_source_quality == "valid"
    assert snap.recovery_gate_reason == "recovery_signal_insufficient"
