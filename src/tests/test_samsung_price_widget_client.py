from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

_WIDGET_PATH = (
    Path(__file__).resolve().parents[2]
    / "tools"
    / "windows"
    / "samsung_price_widget.py"
)
_INSTALLER_PATH = (
    Path(__file__).resolve().parents[2]
    / "tools"
    / "windows"
    / "Install-SamsungPriceWidget.ps1"
)
_SPEC = importlib.util.spec_from_file_location("samsung_price_widget", _WIDGET_PATH)
assert _SPEC and _SPEC.loader
widget = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = widget
_SPEC.loader.exec_module(widget)


def _fresh_advisory_payload(payload: dict) -> tuple[dict, datetime]:
    now = datetime.now().astimezone()
    payload["observed_at_kst"] = now.isoformat()
    advisory = payload["advisory"]
    advisory["observed_at"] = now.isoformat()
    advisory["valid_until"] = (now + timedelta(seconds=60)).isoformat()
    advisory["session"] = "KRX_REGULAR"
    payload.setdefault("market_venue", "KRX")
    payload.setdefault("market_cohort", "KRX")
    payload.setdefault("market_session", "krx_or_closed")
    return payload, now


def _attach_exit_advisory(payload: dict, now: datetime, *, state: str) -> dict:
    payload["exit_advisory"] = {
        "state": state,
        "session": "KRX_REGULAR",
        "reference_exit_price": 220_500 if state != "EXIT_CANCELLED" else None,
        "peak_price": 224_000 if state != "EXIT_CANCELLED" else None,
        "peak_drawdown_pct": 1.56 if state != "EXIT_CANCELLED" else None,
        "broken_support": 221_000 if state != "EXIT_CANCELLED" else None,
        "reasons": ["broken_support_reclaim_failed"],
        "unmet_conditions": [],
        "observed_at": now.isoformat(),
        "valid_until": (now + timedelta(seconds=60)).isoformat(),
        "source_quality": {"status": "PASS", "issues": []},
        "holding_independent": True,
        "future_prediction": False,
        "authority": "widget_advisory_only",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    return payload


def test_widget_payload_parser_accepts_positive_current_price():
    quote = widget.parse_quote_payload(
        {
            "status": "ok",
            "current_price": 71200,
            "day_low_delta": 400,
            "day_low_delta_pct": 0.56,
            "minute_trend": "up",
            "minute_trends": {"1m": "up", "3m": "flat", "5m": "down"},
            "minute_chart": [
                {"time_kst": "10:00", "close": 70000},
                {"time_kst": "10:01", "close": 70500},
            ],
        }
    )

    assert quote.current_price == 71200
    assert quote.day_low_delta == 400
    assert quote.minute_trend == "up"
    assert quote.minute_trend_3m == "flat"
    assert quote.minute_trend_5m == "down"
    assert quote.minute_chart[-1] == ("10:01", 70500)


def test_widget_payload_parser_keeps_legacy_trend_response_compatible():
    quote = widget.parse_quote_payload(
        {
            "status": "ok",
            "current_price": 71200,
            "minute_trend": "down",
            "minute_chart": [],
        }
    )

    assert quote.minute_trend == "down"
    assert quote.minute_trend_3m == "unavailable"
    assert quote.minute_trend_5m == "unavailable"


def test_widget_payload_parser_preserves_nxt_venue():
    quote = widget.parse_quote_payload(
        {
            "status": "ok",
            "current_price": 221500,
            "day_low_delta": 3000,
            "day_low_delta_pct": 1.37,
            "minute_trend": "up",
            "minute_chart": [],
            "market_venue": "NXT",
            "market_session": "nxt_aftermarket",
        }
    )

    assert quote.market_venue == "NXT"
    assert quote.market_session == "nxt_aftermarket"


def test_widget_payload_parser_preserves_premarket_venue():
    quote = widget.parse_quote_payload(
        {
            "status": "ok",
            "current_price": 221500,
            "day_low_delta": 3000,
            "day_low_delta_pct": 1.37,
            "minute_trend": "up",
            "minute_chart": [],
            "market_venue": "NXT",
            "market_cohort": "PREMARKET_KRX_LIKE",
            "market_session": "krx_like_premarket",
        }
    )

    assert quote.market_venue == "NXT"
    assert quote.market_cohort == "PREMARKET_KRX_LIKE"
    assert quote.market_session == "krx_like_premarket"


def test_widget_payload_parser_accepts_safe_advisory_contract():
    payload, now = _fresh_advisory_payload(
        {
            "status": "ok",
            "current_price": 221500,
            "minute_chart": [],
            "advisory": {
                "state": "ENTRY_CAUTION",
                "entry_price_low": 221000,
                "entry_price_high": 221500,
                "reasons": ["vwap_or_resistance_reclaimed"],
                "unmet_conditions": [],
                "trend_assessment": {
                    "state": "TREND_STABLE",
                    "future_prediction": False,
                },
                "external_risk": {"level": "CAUTION"},
                "external_points": {"NQ": {"quality": "BEST_EFFORT_DELAYED"}},
                "authority": "widget_advisory_only",
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
        }
    )
    quote = widget.parse_quote_payload(payload, received_at=now)

    assert quote.advisory_state == "ENTRY_CAUTION"
    assert quote.trend_assessment_state == "TREND_STABLE"
    assert quote.entry_price_low == 221000
    assert quote.external_risk_level == "CAUTION"
    assert quote.external_quality == "DELAYED"


def test_widget_payload_parser_accepts_holding_independent_exit_ready():
    payload, now = _fresh_advisory_payload(
        {
            "status": "ok",
            "current_price": 220_500,
            "minute_chart": [],
            "advisory": {
                "state": "WATCH",
                "authority": "widget_advisory_only",
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
        }
    )
    _attach_exit_advisory(payload, now, state="EXIT_READY")

    quote = widget.parse_quote_payload(payload, received_at=now)

    assert quote.exit_advisory_state == "EXIT_READY"
    assert quote.reference_exit_price == 220_500
    assert quote.exit_peak_price == 224_000
    assert quote.exit_peak_drawdown_pct == 1.56
    assert quote.exit_broken_support == 221_000


def test_widget_payload_parser_rejects_exit_runtime_authority():
    payload, now = _fresh_advisory_payload(
        {
            "status": "ok",
            "current_price": 220_500,
            "minute_chart": [],
            "advisory": {
                "state": "WATCH",
                "authority": "widget_advisory_only",
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
        }
    )
    _attach_exit_advisory(payload, now, state="EXIT_READY")
    payload["exit_advisory"]["runtime_effect"] = True

    with pytest.raises(ValueError, match="invalid_exit_advisory_authority"):
        widget.parse_quote_payload(payload, received_at=now)


def test_widget_payload_parser_rejects_actionable_exit_without_pass_source():
    payload, now = _fresh_advisory_payload(
        {
            "status": "ok",
            "current_price": 220_500,
            "minute_chart": [],
            "advisory": {
                "state": "WATCH",
                "authority": "widget_advisory_only",
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
        }
    )
    _attach_exit_advisory(payload, now, state="EXIT_READY")
    payload["exit_advisory"]["source_quality"]["status"] = "BLOCKED"

    with pytest.raises(ValueError, match="invalid_actionable_exit_advisory"):
        widget.parse_quote_payload(payload, received_at=now)


def test_widget_payload_parser_rejects_exit_session_mismatch():
    payload, now = _fresh_advisory_payload(
        {
            "status": "ok",
            "current_price": 220_500,
            "minute_chart": [],
            "advisory": {
                "state": "WATCH",
                "authority": "widget_advisory_only",
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
        }
    )
    _attach_exit_advisory(payload, now, state="EXIT_READY")
    payload["exit_advisory"]["session"] = "NXT_AFTERMARKET"

    with pytest.raises(ValueError, match="exit_advisory_session_mismatch"):
        widget.parse_quote_payload(payload, received_at=now)


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("reference_exit_price", True, "invalid_reference_exit_price"),
        ("peak_drawdown_pct", float("nan"), "invalid_exit_peak_drawdown_pct"),
        ("peak_drawdown_pct", float("inf"), "invalid_exit_peak_drawdown_pct"),
    ],
)
def test_widget_payload_parser_rejects_malformed_exit_numbers(
    field: str, value: object, error: str
):
    payload, now = _fresh_advisory_payload(
        {
            "status": "ok",
            "current_price": 220_500,
            "minute_chart": [],
            "advisory": {
                "state": "WATCH",
                "authority": "widget_advisory_only",
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
        }
    )
    _attach_exit_advisory(payload, now, state="EXIT_READY")
    payload["exit_advisory"][field] = value

    with pytest.raises(ValueError, match=error):
        widget.parse_quote_payload(payload, received_at=now)


def test_widget_watch_detail_prefers_blocker_over_passed_reason():
    payload, now = _fresh_advisory_payload(
        {
            "status": "ok",
            "current_price": 221500,
            "minute_chart": [],
            "advisory": {
                "state": "WATCH",
                "reasons": ["low_structure_confirmed"],
                "unmet_conditions": ["relative_strength_weak"],
                "authority": "widget_advisory_only",
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
        }
    )
    quote = widget.parse_quote_payload(payload, received_at=now)

    assert widget.primary_advisory_reason(quote) == "relative_strength_weak"
    assert widget.advisory_range_text(quote) == " · 가격대기"


def test_widget_explains_nonactionable_price_range_absence():
    expected = {
        "DATA_WAIT": " · 가격대기",
        "WATCH": " · 가격대기",
        "NO_CHASE": " · 범위이탈",
        "AVOID": " · 범위없음",
    }
    for state, label in expected.items():
        payload, now = _fresh_advisory_payload(
            {
                "status": "ok",
                "current_price": 221_500,
                "minute_chart": [],
                "advisory": {
                    "state": state,
                    "authority": "widget_advisory_only",
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            }
        )

        quote = widget.parse_quote_payload(payload, received_at=now)

        assert widget.advisory_range_text(quote) == label


def test_widget_rejects_stale_actionable_advisory():
    payload, now = _fresh_advisory_payload(
        {
            "status": "ok",
            "current_price": 221500,
            "minute_chart": [],
            "advisory": {
                "state": "ENTRY_READY",
                "entry_price_low": 221000,
                "entry_price_high": 221500,
                "authority": "widget_advisory_only",
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
        }
    )
    stale = now - timedelta(seconds=26)
    payload["observed_at_kst"] = stale.isoformat()
    payload["advisory"]["observed_at"] = stale.isoformat()

    with pytest.raises(ValueError, match="stale_advisory_snapshot"):
        widget.parse_quote_payload(payload, received_at=now)


def test_widget_rejects_session_mismatched_advisory():
    payload, now = _fresh_advisory_payload(
        {
            "status": "ok",
            "current_price": 221500,
            "minute_chart": [],
            "advisory": {
                "state": "WATCH",
                "authority": "widget_advisory_only",
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
        }
    )
    payload["advisory"]["session"] = "NXT_AFTERMARKET"

    with pytest.raises(ValueError, match="advisory_session_mismatch"):
        widget.parse_quote_payload(payload, received_at=now)


def test_widget_accepts_nonactionable_transition_session():
    payload, now = _fresh_advisory_payload(
        {
            "status": "ok",
            "current_price": 221500,
            "minute_chart": [],
            "advisory": {
                "state": "DATA_WAIT",
                "authority": "widget_advisory_only",
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
        }
    )
    payload["advisory"]["session"] = "SESSION_TRANSITION"

    quote = widget.parse_quote_payload(payload, received_at=now)

    assert quote.advisory_state == "DATA_WAIT"


def test_widget_payload_parser_rejects_runtime_effect_advisory():
    with pytest.raises(ValueError, match="invalid_advisory_authority"):
        widget.parse_quote_payload(
            {
                "status": "ok",
                "current_price": 221500,
                "minute_chart": [],
                "advisory": {
                    "state": "ENTRY_READY",
                    "authority": "widget_advisory_only",
                    "runtime_effect": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            }
        )


def test_widget_payload_parser_rejects_negative_advisory_price():
    with pytest.raises(ValueError, match="invalid_entry_price_low"):
        widget.parse_quote_payload(
            {
                "status": "ok",
                "current_price": 221500,
                "minute_chart": [],
                "advisory": {
                    "state": "ENTRY_CAUTION",
                    "entry_price_low": -221000,
                    "authority": "widget_advisory_only",
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            }
        )


def test_widget_payload_parser_rejects_unconfirmed_watch_price_range():
    with pytest.raises(ValueError, match="invalid_non_actionable_entry_price_range"):
        widget.parse_quote_payload(
            {
                "status": "ok",
                "current_price": 221500,
                "minute_chart": [],
                "advisory": {
                    "state": "WATCH",
                    "entry_price_low": 221000,
                    "entry_price_high": 221500,
                    "authority": "widget_advisory_only",
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            }
        )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"status": "unavailable", "current_price": 71200},
        {"status": "ok", "current_price": 0},
        {"status": "ok", "current_price": "not-a-number"},
    ],
)
def test_widget_payload_parser_fails_closed_for_invalid_quotes(payload):
    with pytest.raises(ValueError):
        widget.parse_quote_payload(payload)


def test_widget_requires_https_and_access_key():
    assert widget.validate_settings(widget.WidgetSettings("", "")) == "설정 필요"
    assert (
        widget.validate_settings(widget.WidgetSettings("http://example.test", "key"))
        == "HTTPS URL 필요"
    )
    assert (
        widget.validate_settings(widget.WidgetSettings("https://example.test", "key"))
        is None
    )


def test_widget_refreshes_every_10_seconds():
    assert widget.POLL_INTERVAL_MS == 10_000


def test_windows_installer_uses_a_resolved_ascii_shortcut_path():
    installer = _INSTALLER_PATH.read_text(encoding="utf-8")

    assert "[Environment+SpecialFolder]::DesktopDirectory" in installer
    assert "'SamsungPriceWidget.lnk'" in installer
    assert "CreateShortcut([string]$shortcutPath)" in installer
