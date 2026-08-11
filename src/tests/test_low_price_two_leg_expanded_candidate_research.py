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


def test_expanded_profiles_separate_new_symbols_and_inactive_existing_sessions():
    assert len(expanded.NEW_SYMBOL_PROFILES) == 18
    assert len(expanded.RESEARCH_PROFILES) == 19
    assert set(expanded.CANDIDATE_SYMBOLS).isdisjoint(
        profile.symbol for profile in PROFILES.values()
    )
    assert {
        (profile.symbol, profile.session)
        for profile in expanded.NEW_SYMBOL_PROFILES.values()
    } == {
        (symbol, session)
        for symbol in expanded.CANDIDATE_SYMBOLS
        for session in ("midday", "afternoon")
    }
    assert set(expanded.EXISTING_SYMBOL_TIME_EXTENSION_PROFILES) == {
        "existing_475150_afternoon"
    }
    existing_profile = expanded.EXISTING_SYMBOL_TIME_EXTENSION_PROFILES[
        "existing_475150_afternoon"
    ]
    assert existing_profile.discovery_lane == "existing_symbol_time_extension"
    assert (existing_profile.symbol, existing_profile.session) not in (
        expanded.ACTIVE_SYMBOL_SESSIONS
    )


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
    start_date = expanded.CLEAN_BASELINE_DATE
    trading_dates = list(expanded.clean_baseline_trading_dates(end_date))
    monkeypatch.setattr(
        expanded,
        "build_day_contexts",
        lambda bars: {item: object() for item in trading_dates},
    )
    monkeypatch.setattr(
        expanded,
        "select_profile_spot",
        lambda profile, contexts, **kwargs: {
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
        for symbol in expanded.RESEARCH_SYMBOLS
    }

    report = expanded.build_report(
        sources=sources,
        start_date=start_date,
        end_date=end_date,
    )

    assert report["status"] == "no_qualified_candidate"
    assert len(report["profiles"]) == len(expanded.RESEARCH_PROFILES)
    assert report["trading_date_count"] == 47
    assert report["calibration_trading_day_count"] == 31
    assert report["holdout_trading_day_count"] == 16
    assert report["existing_symbol_time_extension_profile_count"] == 1
    assert report["recommendation_count"] == 0
    assert report["runtime_effect"] is False


def test_daily_window_expands_from_clean_baseline_and_keeps_latest_16_holdout():
    dates_0810 = expanded.clean_baseline_trading_dates(date(2026, 8, 10))
    dates_0811 = expanded.clean_baseline_trading_dates(date(2026, 8, 11))

    assert len(dates_0810) == 46
    assert len(dates_0811) == 47
    assert dates_0810[0] == dates_0811[0] == date(2026, 6, 5)
    assert dates_0811[-1] == date(2026, 8, 11)
    assert len(dates_0811[: -expanded.HOLDOUT_DAYS]) == 31
    assert len(dates_0811[-expanded.HOLDOUT_DAYS :]) == 16
    with pytest.raises(ValueError, match="target_date_not_krx_trading_day"):
        expanded.clean_baseline_trading_dates(date(2026, 8, 9))


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
        "candidate_080220_afternoon": _profile_result(
            symbol="080220",
            name="제주반도체",
            session="afternoon",
            candidate_ev=0.08,
            baseline_ev=0.01,
        ),
        "candidate_017670_midday": _profile_result(
            symbol="017670",
            name="SK텔레콤",
            session="midday",
            candidate_ev=0.03,
            baseline_ev=0.01,
        ),
        "candidate_007660_afternoon": _profile_result(
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

    assert [row["profile_id"] for row in rows] == [
        "candidate_080220_afternoon",
        "candidate_017670_midday",
    ]
    assert rows[0]["price_band"] == "under_50000_krw"
    assert rows[1]["price_band"] == "50000_to_100000_krw"
    assert rows[0]["ev_uplift_pct_point"] == pytest.approx(0.07)
    assert all(row["runtime_effect"] is False for row in rows)


def test_existing_symbol_time_extension_recommendation_preserves_active_profile_lineage():
    profiles = {
        "existing_475150_afternoon": _profile_result(
            symbol="475150",
            name="SK이터닉스",
            session="afternoon",
            candidate_ev=0.08,
            baseline_ev=0.01,
        )
    }

    rows = expanded._recommendation_rows(
        profiles, {"475150": {"latest_close_price": 25_000}}
    )

    assert len(rows) == 1
    assert rows[0]["discovery_lane"] == "existing_symbol_time_extension"
    assert rows[0]["active_profile_ids_for_symbol"] == ["sk_eternix_midday"]
    assert (rows[0]["symbol"], rows[0]["session"]) not in (
        expanded.ACTIVE_SYMBOL_SESSIONS
    )


def _notification_report(recommendations: list[dict] | None = None) -> dict:
    rows = recommendations or []
    new_rows = [row for row in rows if row.get("discovery_lane") == "new_symbol"]
    existing_rows = [
        row
        for row in rows
        if row.get("discovery_lane") == "existing_symbol_time_extension"
    ]
    return {
        "schema": expanded.REPORT_SCHEMA,
        "report_type": expanded.REPORT_TYPE,
        "status": "recommendations_ready" if rows else "no_qualified_candidate",
        "authority": expanded.AUTHORITY,
        "target_date": "2026-08-11",
        "clean_tuning_baseline_date": "2026-06-05",
        "start_date": "2026-06-05",
        "end_date": "2026-08-11",
        "trading_date_count": 47,
        "calibration_trading_day_count": 31,
        "holdout_trading_day_count": 16,
        "candidate_universe_size": len(expanded.CANDIDATE_SYMBOLS),
        "existing_symbol_universe_size": len(expanded.IMPLEMENTED_SYMBOLS),
        "source_symbol_count": len(expanded.RESEARCH_SYMBOLS),
        "new_symbol_profile_count": len(expanded.NEW_SYMBOL_PROFILES),
        "existing_symbol_time_extension_profile_count": len(
            expanded.EXISTING_SYMBOL_TIME_EXTENSION_PROFILES
        ),
        "recommendation_count": len(rows),
        "recommendations": rows,
        "new_symbol_recommendations": new_rows,
        "new_symbol_recommendation_count": len(new_rows),
        "existing_symbol_time_extension_recommendations": existing_rows,
        "existing_symbol_time_extension_recommendation_count": len(existing_rows),
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


def test_telegram_message_separates_new_symbol_and_existing_time_extension_lanes():
    rows = expanded._recommendation_rows(
        {
            "candidate_080220_afternoon": _profile_result(
                symbol="080220",
                name="제주반도체",
                session="afternoon",
                candidate_ev=0.08,
                baseline_ev=0.01,
            ),
            "existing_475150_afternoon": _profile_result(
                symbol="475150",
                name="SK이터닉스",
                session="afternoon",
                candidate_ev=0.07,
                baseline_ev=0.01,
            ),
        },
        {
            "080220": {"latest_close_price": 24_000},
            "475150": {"latest_close_price": 25_000},
        },
    )

    message = expanded.build_telegram_message(_notification_report(rows))

    assert "[신규 종목]" in message
    assert "[기존 종목·신규 시간대]" in message
    assert "제주반도체(080220)" in message
    assert "SK이터닉스(475150)" in message


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
    report["start_date"] = "2026-06-08"
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
        start_date=date(2026, 6, 5),
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
