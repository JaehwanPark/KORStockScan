from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from src.engine.monitoring import (
    low_price_two_leg_expanded_candidate_research as expanded,
)
from src.engine.monitoring.low_price_two_leg_entry_spot_research import (
    ResearchError,
    fetch_sor_history,
)
from src.trading.low_price_two_leg.profiles import PROFILES


class FakeResponse:
    status_code = 200
    headers = {}

    def __init__(self, rows):
        self._rows = rows

    def json(self):
        return {"return_code": 0, "stk_min_pole_chart_qry": self._rows}


def test_expanded_profiles_are_research_only_and_disjoint_from_live_symbols():
    assert len(expanded.RESEARCH_PROFILES) == 18
    assert set(expanded.CANDIDATE_SYMBOLS).isdisjoint(
        profile.symbol for profile in PROFILES.values()
    )
    assert {
        (profile.symbol, profile.session)
        for profile in expanded.RESEARCH_PROFILES.values()
    } == {
        (symbol, session)
        for symbol in expanded.CANDIDATE_SYMBOLS
        for session in ("midday", "afternoon")
    }


def test_fetch_expanded_symbol_requires_explicit_research_allowlist():
    started = date(2026, 6, 5)
    dates = [started + timedelta(days=index) for index in range(46)]
    rows = [
        {
            "cntr_tm": f"{item.strftime('%Y%m%d')}131500",
            "open_pric": "20000",
            "high_pric": "20100",
            "low_pric": "19900",
            "cur_prc": "20000",
        }
        for item in dates
    ]
    rows.append(
        {
            "cntr_tm": "20260604131500",
            "open_pric": "20000",
            "high_pric": "20100",
            "low_pric": "19900",
            "cur_prc": "20000",
        }
    )

    with pytest.raises(ValueError, match="symbol_not_in_selected_profile_allowlist"):
        fetch_sor_history(
            symbol="015760",
            token="TOKEN",
            start_date=started,
            end_date=dates[-1],
            post=lambda *args, **kwargs: FakeResponse(rows),
        )

    bars, meta = fetch_sor_history(
        symbol="015760",
        token="TOKEN",
        start_date=started,
        end_date=dates[-1],
        post=lambda *args, **kwargs: FakeResponse(rows),
        allowed_symbols=frozenset({"015760"}),
    )
    assert len(bars) == 46
    assert meta["source_quality_status"] == "PASS"


def test_expanded_report_fails_closed_on_incomplete_source_universe():
    with pytest.raises(ResearchError, match="expanded_candidate_source_set_mismatch"):
        expanded.build_report(
            sources={},
            start_date=expanded.CLEAN_BASELINE_DATE,
            end_date=date(2026, 8, 10),
        )


def test_expanded_report_builds_daily_artifact_for_complete_source_universe(
    monkeypatch,
):
    end_date = date(2026, 8, 11)
    start_date = expanded.rolling_window_start(end_date)
    trading_dates = []
    current = start_date
    while current <= end_date:
        if expanded.is_krx_trading_day(current):
            trading_dates.append(current)
        current += timedelta(days=1)
    monkeypatch.setattr(
        expanded,
        "build_day_contexts",
        lambda bars: {item: object() for item in trading_dates},
    )
    monkeypatch.setattr(
        expanded,
        "select_profile_spot",
        lambda profile, contexts: {
            "symbol": profile.symbol,
            "name": profile.name,
            "session": profile.session,
            "decision": "no_calibration_candidate",
            "recommended_spot": None,
            "baseline": {
                "holdout": {
                    "signal_episodes": 0,
                    "completed_legs": 0,
                    "held_legs": 0,
                    "notional_weighted_ev_pct": None,
                }
            },
        },
    )
    sources = {
        symbol: (
            [SimpleNamespace(close_price=20_000)],
            {"source_quality_status": "PASS"},
        )
        for symbol in expanded.CANDIDATE_SYMBOLS
    }

    report = expanded.build_report(
        sources=sources,
        start_date=start_date,
        end_date=end_date,
    )

    assert report["status"] == "no_qualified_candidate"
    assert len(report["profiles"]) == len(expanded.RESEARCH_PROFILES)
    assert report["recommendation_count"] == 0
    assert report["runtime_effect"] is False


def test_daily_rolling_window_stays_inside_clean_baseline():
    assert expanded.rolling_window_start(date(2026, 8, 10)) == date(2026, 6, 5)
    assert expanded.rolling_window_start(date(2026, 8, 11)) == date(2026, 6, 8)
    with pytest.raises(ValueError, match="target_date_not_krx_trading_day"):
        expanded.rolling_window_start(date(2026, 8, 9))


def _profile_result(
    *,
    symbol: str,
    name: str,
    session: str,
    candidate_ev: float,
    baseline_ev: float,
) -> dict:
    return {
        "symbol": symbol,
        "name": name,
        "session": session,
        "decision": "holdout_pass_source_only_early_candidate",
        "recommended_spot": {
            "scan_start": "14:15",
            "scan_end": "14:24",
            "lookback_bars": 15,
            "rolling_high_drawdown_pct": 1.5,
            "rolling_low_proximity_pct": 0.2,
        },
        "selected": {
            "holdout": {
                "signal_episodes": 4,
                "completed_legs": 7,
                "held_legs": 0,
                "notional_weighted_ev_pct": candidate_ev,
            }
        },
        "baseline": {"holdout": {"notional_weighted_ev_pct": baseline_ev}},
    }


def test_recommendations_rank_profiles_and_enforce_daily_price_cap():
    profiles = {
        "under_50k": _profile_result(
            symbol="080220",
            name="제주반도체",
            session="afternoon",
            candidate_ev=0.08,
            baseline_ev=0.01,
        ),
        "under_100k": _profile_result(
            symbol="017670",
            name="SK텔레콤",
            session="midday",
            candidate_ev=0.03,
            baseline_ev=0.01,
        ),
        "price_cap": _profile_result(
            symbol="007660",
            name="이수페타시스",
            session="afternoon",
            candidate_ev=0.50,
            baseline_ev=0.01,
        ),
    }
    source_meta = {
        "080220": {"latest_close_price": 24_000},
        "017670": {"latest_close_price": 65_000},
        "007660": {"latest_close_price": 100_500},
    }

    rows = expanded._recommendation_rows(profiles, source_meta)

    assert [row["profile_id"] for row in rows] == ["under_50k", "under_100k"]
    assert rows[0]["price_band"] == "under_50000_krw"
    assert rows[1]["price_band"] == "50000_to_100000_krw"
    assert rows[0]["ev_uplift_pct_point"] == pytest.approx(0.07)
    assert all(row["runtime_effect"] is False for row in rows)


def _notification_report(recommendations: list[dict] | None = None) -> dict:
    rows = recommendations or []
    return {
        "schema": expanded.REPORT_SCHEMA,
        "report_type": expanded.REPORT_TYPE,
        "status": "recommendations_ready" if rows else "no_qualified_candidate",
        "authority": expanded.AUTHORITY,
        "target_date": "2026-08-11",
        "start_date": "2026-06-08",
        "end_date": "2026-08-11",
        "candidate_universe_size": len(expanded.CANDIDATE_SYMBOLS),
        "recommendation_count": len(rows),
        "recommendations": rows,
        "metric_contract": expanded.METRIC_CONTRACT,
        "recommendation_only": True,
        "machine_created": False,
        "service_started": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def test_admin_notifier_retries_sends_once_and_never_creates_machine(tmp_path):
    attempts = []
    sleeps = []

    def sender(token, admin_id, message):
        attempts.append((token, admin_id, message))
        if len(attempts) < 3:
            raise OSError("temporary telegram failure")

    notifier = expanded.CandidateRecommendationNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("token", "admin"),
        sender=sender,
        enabled=True,
        max_attempts=3,
        retry_delay_sec=0.5,
        sleeper=sleeps.append,
    )
    report = _notification_report()

    assert notifier.notify(report) == "sent"
    assert notifier.notify(report) == "duplicate"
    assert len(attempts) == 3
    assert sleeps == [0.5, 0.5]
    assert "자동 기계 구현·기동·실주문 권한 없음" in attempts[-1][2]
    state = (tmp_path / "state.json").read_text(encoding="utf-8")
    assert '"machine_created": false' in state
    assert '"service_started": false' in state


def test_admin_notifier_fails_closed_for_invalid_authority(tmp_path):
    report = _notification_report()
    report["runtime_effect"] = True
    notifier = expanded.CandidateRecommendationNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("token", "admin"),
        sender=lambda *args: pytest.fail("invalid report must not be sent"),
        enabled=True,
    )

    assert notifier.notify(report) == "invalid_report"

    report = _notification_report()
    report["status"] = "recommendations_ready"
    assert notifier.notify(report) == "invalid_report"

    report = _notification_report()
    report["start_date"] = "2026-06-05"
    assert notifier.notify(report) == "invalid_report"


def test_admin_notifier_exposes_exhausted_delivery_retries(tmp_path):
    attempts = []

    def sender(*args):
        attempts.append(args)
        raise OSError("telegram unavailable")

    notifier = expanded.CandidateRecommendationNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("token", "admin"),
        sender=sender,
        enabled=True,
        max_attempts=3,
        retry_delay_sec=0,
        sleeper=lambda _: None,
    )

    assert notifier.notify(_notification_report()) == "send_failed"
    assert len(attempts) == 3
    assert not (tmp_path / "state.json").exists()


def test_default_target_date_never_uses_an_incomplete_regular_session():
    assert expanded._default_target_date(
        now=expanded.datetime(2026, 8, 11, 14, 0, tzinfo=expanded.KST)
    ) == date(2026, 8, 10)
    assert expanded._default_target_date(
        now=expanded.datetime(2026, 8, 11, 20, 10, tzinfo=expanded.KST)
    ) == date(2026, 8, 11)


def test_source_quality_blocked_result_is_reported_to_admin_without_recommendation(
    tmp_path,
):
    report = expanded.build_source_quality_blocked_report(
        start_date=date(2026, 6, 8),
        end_date=date(2026, 8, 11),
        reason="015760_source_quality_fail",
    )
    report["telegram_status"] = "not_requested"
    sent = []
    notifier = expanded.CandidateRecommendationNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("token", "admin"),
        sender=lambda token, admin, message: sent.append(message),
        enabled=True,
    )

    assert report["status"] == "source_quality_blocked"
    assert report["recommendations"] == []
    assert notifier.notify(report) == "sent"
    assert "source-quality 문제로 신규 추천을 산출하지 않았습니다" in sent[0]
    assert "015760_source_quality_fail" in sent[0]


def test_telegram_transport_requires_explicit_ok_response(monkeypatch):
    class TelegramResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"ok": false, "description": "chat not found"}'

    monkeypatch.setattr(
        expanded.request, "urlopen", lambda request, timeout: TelegramResponse()
    )

    with pytest.raises(RuntimeError, match="telegram_send_not_ok"):
        expanded._send_telegram("token", "admin", "message")


def test_daily_network_failure_becomes_source_quality_admin_artifact(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        expanded.kiwoom_utils, "get_cached_kiwoom_token", lambda: "TOKEN"
    )

    def fail_fetch(**kwargs):
        raise expanded.requests.ConnectionError("network unavailable")

    monkeypatch.setattr(expanded, "fetch_sor_history", fail_fetch)

    assert (
        expanded.main(
            [
                "--target-date",
                "2026-08-11",
                "--output-dir",
                str(tmp_path),
                "--write",
            ]
        )
        == 0
    )
    report = expanded.json.loads(
        (
            tmp_path / "low_price_two_leg_expanded_candidate_research_2026-08-11.json"
        ).read_text(encoding="utf-8")
    )
    assert report["status"] == "source_quality_blocked"
    assert report["telegram_status"] == "not_requested"
    assert "network unavailable" in report["source_quality_reasons"][0]
