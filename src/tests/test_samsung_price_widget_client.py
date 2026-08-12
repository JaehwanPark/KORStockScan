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
_GUNICORN_WIDGET_DROPIN_PATH = (
    Path(__file__).resolve().parents[2]
    / "deploy"
    / "systemd"
    / "korstockscan-gunicorn-widget.conf"
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
    assert quote.holding_status == "UNAVAILABLE"
    assert quote.holding_quantity is None
    assert quote.day_low_delta == 400
    assert quote.minute_trend == "up"
    assert quote.minute_trend_3m == "flat"
    assert quote.minute_trend_5m == "down"
    assert quote.minute_chart[-1] == ("10:01", 70500)


def test_widget_payload_parser_accepts_fresh_ws_price_comparison():
    now = datetime.now().astimezone()
    quote = widget.parse_quote_payload(
        {
            "status": "ok",
            "current_price": 242_000,
            "minute_chart": [],
            "websocket_comparison": {
                "status": "OK",
                "current_price": 242_500,
                "reference_price": 242_000,
                "price_delta": 500,
                "observed_at_kst": (now - timedelta(seconds=0.4)).isoformat(),
                "market_route": "SOR",
                "authority": "widget_ws_price_comparison_only",
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "used_for_manual_order": False,
            },
        },
        received_at=now,
    )

    assert quote.websocket_status == "OK"
    assert quote.websocket_price == 242_500
    assert quote.websocket_price_delta == 500
    assert quote.websocket_route == "SOR"
    assert 390 <= quote.websocket_age_ms <= 410


def test_widget_payload_parser_ignores_ws_comparison_with_runtime_authority():
    now = datetime.now().astimezone()
    quote = widget.parse_quote_payload(
        {
            "status": "ok",
            "current_price": 242_000,
            "minute_chart": [],
            "websocket_comparison": {
                "status": "OK",
                "current_price": 242_500,
                "reference_price": 242_000,
                "price_delta": 500,
                "observed_at_kst": now.isoformat(),
                "market_route": "SOR",
                "authority": "widget_ws_price_comparison_only",
                "runtime_effect": True,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "used_for_manual_order": False,
            },
        },
        received_at=now,
    )

    assert quote.websocket_status == "UNAVAILABLE"
    assert quote.websocket_price is None


def test_widget_payload_parser_accepts_display_only_position():
    now = datetime.now().astimezone()
    quote = widget.parse_quote_payload(
        {
            "status": "ok",
            "current_price": 231_000,
            "minute_chart": [],
            "position": {
                "status": "OK",
                "symbol": "005930",
                "quantity": 5,
                "average_price": 229_750,
                "observed_at_kst": now.isoformat(),
                "token_mode": "shared_cache_only",
                "account_query_read_only": True,
                "authority": "widget_account_position_display_only",
                "runtime_effect": False,
                "actual_order_submitted": False,
                "position_data_used_for_order_quantity": False,
            },
        },
        received_at=now,
    )

    assert quote.holding_status == "OK"
    assert quote.holding_quantity == 5
    assert quote.holding_average_price == 229_750


def test_widget_payload_parser_does_not_display_malformed_position():
    now = datetime.now().astimezone()
    quote = widget.parse_quote_payload(
        {
            "status": "ok",
            "current_price": 231_000,
            "minute_chart": [],
            "position": {
                "status": "OK",
                "quantity": 5,
                "average_price": None,
                "observed_at_kst": now.isoformat(),
                "token_mode": "shared_cache_only",
                "account_query_read_only": True,
                "authority": "widget_account_position_display_only",
                "runtime_effect": False,
                "actual_order_submitted": False,
                "position_data_used_for_order_quantity": False,
            },
        },
        received_at=now,
    )

    assert quote.holding_status == "UNAVAILABLE"
    assert quote.holding_quantity is None


def test_widget_payload_parser_does_not_display_stale_position():
    now = datetime.now().astimezone()
    quote = widget.parse_quote_payload(
        {
            "status": "ok",
            "current_price": 231_000,
            "minute_chart": [],
            "position": {
                "status": "OK",
                "symbol": "005930",
                "quantity": 5,
                "average_price": 229_750,
                "observed_at_kst": (now - timedelta(seconds=46)).isoformat(),
                "token_mode": "shared_cache_only",
                "account_query_read_only": True,
                "authority": "widget_account_position_display_only",
                "runtime_effect": False,
                "actual_order_submitted": False,
                "position_data_used_for_order_quantity": False,
            },
        },
        received_at=now,
    )

    assert quote.holding_status == "UNAVAILABLE"


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
    assert quote.order_session == "KRX_REGULAR"
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


def test_widget_derives_separate_https_order_endpoint():
    assert (
        widget.order_endpoint_url(
            "https://korstockscan.example/api/widget/samsung-price"
        )
        == "https://korstockscan.example/api/widget/samsung-order"
    )
    with pytest.raises(ValueError, match="invalid_order_endpoint"):
        widget.order_endpoint_url("http://example.test/api/widget/samsung-price")


def test_widget_manual_order_uses_dedicated_key_and_validates_receipt(monkeypatch):
    captured = {}
    request_id = "89725f7c-74e1-4436-88ef-91839579f4f3"

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        @staticmethod
        def read():
            return (
                __import__("json")
                .dumps(
                    {
                        "status": "accepted",
                        "authority": "operator_widget_manual_order_v1",
                        "client_request_id": request_id,
                        "side": "BUY",
                        "quantity": 3,
                        "accepted_order_count": 2,
                        "expected_order_count": 2,
                        "orders": [],
                    }
                )
                .encode("utf-8")
            )

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["body"] = __import__("json").loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(widget, "urlopen", fake_urlopen)
    settings = widget.WidgetSettings(
        "https://korstockscan.example/api/widget/samsung-price",
        "read-key",
        "order-key",
    )

    result = widget.submit_manual_order(
        settings,
        side="BUY",
        quantity=3,
        displayed_price=230_500,
        client_request_id=request_id,
    )

    assert result["status"] == "accepted"
    assert captured["url"].endswith("/api/widget/samsung-order")
    assert captured["headers"]["X-korstockscan-widget-order-key"] == "order-key"
    assert "read-key" not in captured["headers"].values()
    assert captured["body"] == {
        "side": "BUY",
        "quantity": 3,
        "displayed_price": 230_500,
        "client_request_id": request_id,
    }


def test_widget_manual_order_requires_order_key():
    with pytest.raises(RuntimeError, match="주문 키 필요"):
        widget.submit_manual_order(
            widget.WidgetSettings(
                "https://example.test/api/widget/samsung-price", "read-key"
            ),
            side="SELL",
            quantity=1,
            displayed_price=230_500,
            client_request_id="df788734-664c-4fac-9e27-dd4f73e58aa9",
        )


def test_widget_preserves_ambiguous_broker_receipt_from_http_error(monkeypatch):
    request_id = "31b40041-7c03-43e4-bba0-c41c7f22d43f"
    body = (
        __import__("json")
        .dumps(
            {
                "status": "ambiguous",
                "authority": "operator_widget_manual_order_v1",
                "client_request_id": request_id,
                "side": "BUY",
                "quantity": 2,
                "accepted_order_count": 1,
                "expected_order_count": 2,
                "orders": [{"order_no": "ORDER-1", "accepted": True}],
            }
        )
        .encode("utf-8")
    )

    def ambiguous_urlopen(request, timeout):
        raise widget.HTTPError(
            request.full_url,
            502,
            "ambiguous",
            hdrs=None,
            fp=__import__("io").BytesIO(body),
        )

    monkeypatch.setattr(widget, "urlopen", ambiguous_urlopen)
    result = widget.submit_manual_order(
        widget.WidgetSettings(
            "https://example.test/api/widget/samsung-price",
            "read-key",
            "order-key",
        ),
        side="BUY",
        quantity=2,
        displayed_price=230_500,
        client_request_id=request_id,
    )

    assert result["status"] == "ambiguous"
    assert result["orders"][0]["order_no"] == "ORDER-1"


def test_widget_refreshes_every_2_seconds():
    assert widget.POLL_INTERVAL_MS == 2_000


def test_windows_installer_uses_a_resolved_ascii_shortcut_path():
    installer = _INSTALLER_PATH.read_text(encoding="utf-8")

    assert "[Environment+SpecialFolder]::DesktopDirectory" in installer
    assert "'SamsungPriceWidget.lnk'" in installer
    assert "CreateShortcut([string]$shortcutPath)" in installer
    assert "[string]$OrderAccessKey" in installer
    assert "order_access_key = $OrderAccessKey" in installer


def test_gunicorn_widget_dropin_keeps_quote_and_order_keys_separate():
    dropin = _GUNICORN_WIDGET_DROPIN_PATH.read_text(encoding="utf-8")

    assert "KORSTOCKSCAN_SAMSUNG_WIDGET_ACCESS_KEY_FILE=" in dropin
    assert "KORSTOCKSCAN_SAMSUNG_WIDGET_ORDER_KEY_FILE=" in dropin
    assert "samsung-price-widget.key" in dropin
    assert "samsung-price-widget-order.key" in dropin
