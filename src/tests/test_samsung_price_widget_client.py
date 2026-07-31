from __future__ import annotations

import importlib.util
import sys
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
