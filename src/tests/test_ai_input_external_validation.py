import gzip
import json
from datetime import datetime

import pytest
import requests

from src.engine.scalping import ai_input_external_validation as mod


def _minute(minute, close, volume):
    return {
        "source_timestamp": f"20260724{minute.replace(':', '')}00",
        "체결시간": f"{minute}:00",
        "시가": close,
        "고가": close,
        "저가": close,
        "현재가": close,
        "거래량": volume,
    }


def test_payload_context_unwraps_separate_exact_replay_context():
    assert mod._payload_context(
        {
            "exact_payload": {
                "entry_candle_context": {
                    "venue": "KRX",
                    "session": "KRX_REGULAR",
                    "request_code": "005930_KRX",
                    "bars": [{"t": "09:00"}],
                }
            },
            "entry_setup_evidence_v1": {"setup_state": "READY"},
        }
    ) == {
        "context_type": "entry",
        "venue": "KRX",
        "session": "KRX_REGULAR",
        "request_code": "005930_KRX",
        "rest_route": None,
        "bars": [{"t": "09:00"}],
    }


def test_naver_cumulative_volume_requires_consecutive_minutes():
    rows = [
        {"timestamp": "2026-07-24T15:14:00+09:00", "volume": 100},
        {"timestamp": "2026-07-24T15:15:00+09:00", "volume": 120},
        {"timestamp": "2026-07-24T15:17:00+09:00", "volume": 150},
    ]

    deltas = mod.naver_minute_volume_deltas(rows)

    assert deltas["15:15"]["delta"] == 20
    assert deltas["15:15"]["comparable"] is True
    assert deltas["15:17"]["comparable"] is False


def test_current_trading_day_daily_bar_and_forming_minute_are_not_compared():
    def live_minute(minute, close, volume):
        return {
            "source_timestamp": f"20260727{minute.replace(':', '')}00",
            "체결시간": f"{minute}:00",
            "시가": close,
            "고가": close,
            "저가": close,
            "현재가": close,
            "거래량": volume,
        }

    result = mod.build_symbol_comparison(
        symbol="005930",
        venue="KRX",
        target_date="2026-07-27",
        kiwoom_daily={
            "open": 100,
            "high": 110,
            "low": 90,
            "close": 105,
            "volume": 1000,
        },
        kiwoom_minutes=[
            live_minute("10:27", 100, 10),
            live_minute("10:28", 100, 10),
            live_minute("10:29", 100, 10),
            live_minute("10:30", 999, 20),
        ],
        external_daily={
            "open": 101,
            "high": 111,
            "low": 91,
            "close": 106,
            "volume": 1001,
        },
        naver_minutes=[
            {
                "timestamp": "2026-07-27T10:26:00+09:00",
                "close": 99,
                "volume": 100,
            },
            {
                "timestamp": "2026-07-27T10:27:00+09:00",
                "close": 100,
                "volume": 110,
            },
            {
                "timestamp": "2026-07-27T10:28:00+09:00",
                "close": 100,
                "volume": 120,
            },
            {
                "timestamp": "2026-07-27T10:29:00+09:00",
                "close": 100,
                "volume": 130,
            },
            {
                "timestamp": "2026-07-27T10:30:00+09:00",
                "close": 998,
                "volume": 150,
            },
        ],
        ai_payload_row=None,
        source_meta={},
        as_of=datetime(2026, 7, 27, 10, 30, 30, tzinfo=mod.KST),
    )

    by_field = {row["field"]: row for row in result["comparison_rows"]}
    assert all(
        by_field[f"daily.{field}"]["status"] == "NOT_COMPARABLE"
        for field in ("open", "high", "low", "close", "volume")
    )
    assert all(
        by_field[f"daily.{field}"]["reason"]
        == "current_trading_day_daily_bar_not_final"
        for field in ("open", "high", "low", "close", "volume")
    )
    assert by_field["minute.10:27.close"]["status"] == "MATCH"
    assert by_field["minute.10:27.volume"]["status"] == "MATCH"
    assert by_field["minute.10:29.close"]["status"] == "NOT_COMPARABLE"
    assert (
        by_field["minute.10:29.close"]["reason"]
        == "naver_minute_publication_lag_window"
    )
    assert by_field["minute.10:29.volume"]["status"] == "NOT_COMPARABLE"
    assert by_field["minute.10:30.close"]["status"] == "NOT_COMPARABLE"
    assert (
        by_field["minute.10:30.close"]["reason"]
        == "forming_minute_excluded_exact_capture_cutoff"
    )
    assert by_field["minute.10:30.volume"]["status"] == "NOT_COMPARABLE"
    assert result["summary"]["mismatch_count"] == 0


def test_missing_completed_minute_fails_required_source_quality_gate():
    def source_row(minute):
        return {
            "source_timestamp": f"20260727{minute.replace(':', '')}00",
            "시가": 100,
            "고가": 100,
            "저가": 100,
            "현재가": 100,
            "거래량": 10,
        }

    result = mod.build_symbol_comparison(
        symbol="100090",
        venue="KRX",
        target_date="2026-07-27",
        kiwoom_daily={},
        kiwoom_minutes=[source_row("09:00"), source_row("09:02")],
        external_daily=None,
        naver_minutes=[],
        ai_payload_row=None,
        source_meta={},
        as_of=datetime(2026, 7, 27, 10, 0, tzinfo=mod.KST),
    )

    assert result["summary"]["source_quality_gate_status"] == ("source_quality_blocked")
    assert result["summary"]["required_source_field_match_status"] == "fail"


def test_independent_recalculation_excludes_current_forming_minute():
    rows = [
        {
            "source_timestamp": "20260727090000",
            "시가": 100,
            "고가": 100,
            "저가": 100,
            "현재가": 100,
            "거래량": 10,
        },
        {
            "source_timestamp": "20260727090100",
            "시가": 1000,
            "고가": 1000,
            "저가": 1000,
            "현재가": 1000,
            "거래량": 1000,
        },
    ]

    result = mod._independent_api_observation(
        rows,
        target_date="2026-07-27",
        venue="KRX",
        as_of=datetime(2026, 7, 27, 9, 1, 30, tzinfo=mod.KST),
    )

    assert result["session_bar_vwap"]["value"] == 100.0


def test_opening_call_auction_volume_is_not_compared_as_a_regular_minute():
    result = mod.build_symbol_comparison(
        symbol="005930",
        venue="KRX",
        target_date="2026-07-24",
        kiwoom_daily={},
        kiwoom_minutes=[
            _minute("08:59", 100, 0),
            _minute("09:00", 101, 10),
        ],
        external_daily=None,
        naver_minutes=[
            {
                "timestamp": "2026-07-24T08:59:00+09:00",
                "close": 100,
                "volume": 0,
            },
            {
                "timestamp": "2026-07-24T09:00:00+09:00",
                "close": 101,
                "volume": 15,
            },
        ],
        ai_payload_row=None,
        source_meta={},
    )

    row = next(
        item
        for item in result["comparison_rows"]
        if item["field"] == "minute.09:00.volume"
    )
    assert row["status"] == "NOT_COMPARABLE"
    assert row["reason"] == "krx_opening_call_auction_cumulative_basis"


def test_golden_005930_daily_and_minutes_match_with_call_auction_separated():
    api_minutes = [
        _minute("15:14", 249000, 100),
        _minute("15:15", 249500, 10),
        _minute("15:16", 249500, 20),
        _minute("15:17", 249000, 30),
        _minute("15:18", 249500, 40),
        _minute("15:19", 249500, 50),
        _minute("15:30", 249500, 1000),
    ]
    cumulative = [1000, 1010, 1030, 1060, 1100, 1150, 2832]
    naver_minutes = [
        {
            "timestamp": f"2026-07-24T{minute}:00+09:00",
            "close": close,
            "volume": volume,
        }
        for minute, close, volume in zip(
            ["15:14", "15:15", "15:16", "15:17", "15:18", "15:19", "15:30"],
            [249000, 249500, 249500, 249000, 249500, 249500, 249500],
            cumulative,
        )
    ]

    result = mod.build_symbol_comparison(
        symbol="005930",
        venue="KRX",
        target_date="2026-07-24",
        kiwoom_daily={
            "open": 266000,
            "high": 266500,
            "low": 247000,
            "close": 249500,
            "volume": 26175580,
        },
        kiwoom_minutes=api_minutes,
        external_daily={
            "open": 266000,
            "high": 266500,
            "low": 247000,
            "close": 249500,
            "volume": 26175580,
        },
        naver_minutes=naver_minutes,
        ai_payload_row=None,
        source_meta={},
    )

    assert result["summary"]["mismatch_count"] == 0
    statuses = {
        row["field"]: (row["status"], row["reason"])
        for row in result["comparison_rows"]
    }
    for minute in ("15:15", "15:16", "15:17", "15:18", "15:19"):
        assert statuses[f"minute.{minute}.close"][0] == "MATCH"
        assert statuses[f"minute.{minute}.volume"][0] == "MATCH"
    assert statuses["minute.15:30.close"] == (
        "NOT_COMPARABLE",
        "krx_closing_call_auction_separate_aggregation",
    )
    assert statuses["minute.15:30.volume"] == (
        "NOT_COMPARABLE",
        "krx_closing_call_auction_separate_aggregation",
    )


def test_compare_float_uses_one_e_minus_six_tolerance():
    matched = mod.compare_value(
        field="session_vwap",
        api_raw_value=None,
        normalized_value=100.0000001,
        ai_payload_value=100.0000001,
        external_value=100.0000009,
        value_type="float",
        source="independent_recalculation",
        basis={},
    )
    mismatched = mod.compare_value(
        field="session_vwap",
        api_raw_value=None,
        normalized_value=100.0,
        ai_payload_value=100.0,
        external_value=100.000002,
        value_type="float",
        source="independent_recalculation",
        basis={},
    )

    assert matched["status"] == "MATCH"
    assert mismatched["status"] == "MISMATCH"


def test_request_and_response_provenance_join_by_request_id(tmp_path, monkeypatch):
    request_dir = tmp_path / "requests"
    trace_dir = tmp_path / "traces"
    request_dir.mkdir()
    trace_dir.mkdir()
    monkeypatch.setattr(mod, "REQUEST_DIR", request_dir)
    monkeypatch.setattr(mod, "TRACE_DIR", trace_dir)
    with gzip.open(
        request_dir / "ai_decision_requests_2026-07-24.jsonl.gz",
        "wt",
        encoding="utf-8",
    ) as handle:
        handle.write(
            json.dumps(
                {
                    "request_id": "req-1",
                    "symbol": "005930",
                    "endpoint": "holding_score",
                    "payload_sha256": "a" * 64,
                }
            )
            + "\n"
        )
    with gzip.open(
        trace_dir / "ai_decision_trace_2026-07-24.jsonl.gz",
        "wt",
        encoding="utf-8",
    ) as handle:
        handle.write(
            json.dumps(
                {
                    "request_id": "req-1",
                    "provider_actual": "openai",
                    "provider_response_id": "resp-1",
                    "response_sha256": "b" * 64,
                    "total_tokens": 120,
                }
            )
            + "\n"
        )

    rows = mod.load_request_provenance("2026-07-24")["005930"]

    assert rows[0]["endpoint"] == "holding_score"
    assert rows[0]["provider"] == "openai"
    assert rows[0]["provider_response_id"] == "resp-1"
    assert rows[0]["response_sha256"] == "b" * 64


def test_source_metadata_redacts_auth_fields():
    sanitized = mod._sanitize_metadata(
        {
            "request_code": "005930",
            "Authorization": "Bearer secret",
            "nested": {
                "access_token": "secret-token",
                "refresh_token": "secret-refresh",
                "clientSecret": "secret-client",
                "token_usage": {"input_tokens": 100},
                "note": "cookie=session-secret",
            },
        }
    )

    assert sanitized == {
        "request_code": "005930",
        "Authorization": "[REDACTED]",
        "nested": {
            "access_token": "[REDACTED]",
            "refresh_token": "[REDACTED]",
            "clientSecret": "[REDACTED]",
            "token_usage": {"input_tokens": 100},
            "note": "cookie=[REDACTED]",
        },
    }


def test_krx_open_api_is_not_called_without_auth_key():
    calls = []

    def unexpected_get(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("network must not be called without KRX auth")

    rows, metadata = mod._fetch_krx_daily(
        "2026-07-24",
        auth_key="",
        get=unexpected_get,
    )

    assert rows == {}
    assert calls == []
    assert metadata["status"] == "source_unavailable"
    assert metadata["error"] == "krx_open_api_auth_key_not_configured"
    assert metadata["auth_configured"] is False
    assert metadata["legacy_mdc_endpoint_called"] is False


def test_krx_open_api_config_key_alias_is_resolved_without_exposing_value(
    tmp_path, monkeypatch
):
    config_path = tmp_path / "config_prod.json"
    config_path.write_text(
        json.dumps({"KRX_OPEN_API_KEY": "config-only-secret"}), encoding="utf-8"
    )
    monkeypatch.delenv("KRX_OPEN_API_AUTH_KEY", raising=False)
    monkeypatch.delenv("KRX_OPEN_API_KEY", raising=False)

    key, source = mod._resolve_krx_open_api_auth_key(config_path=config_path)

    assert key == "config-only-secret"
    assert source == "config:KRX_OPEN_API_KEY"
    assert "config-only-secret" not in json.dumps(
        {
            "auth_source": source,
            "auth_configured": bool(key),
        }
    )


def test_krx_open_api_explicit_empty_key_does_not_fall_back_to_config(tmp_path):
    config_path = tmp_path / "config_prod.json"
    config_path.write_text(
        json.dumps({"KRX_OPEN_API_KEY": "config-only-secret"}), encoding="utf-8"
    )

    key, source = mod._resolve_krx_open_api_auth_key(
        auth_key="", config_path=config_path
    )

    assert key == ""
    assert source == "explicit_argument"


def test_krx_open_api_fetches_both_markets_without_recording_auth():
    calls = []

    class Response:
        def __init__(self, row):
            self._row = row

        def raise_for_status(self):
            return None

        def json(self):
            return {"OutBlock_1": [self._row]}

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        symbol = "005930" if url.endswith("/stk_bydd_trd") else "100090"
        return Response(
            {
                "BAS_DD": "20260724",
                "ISU_CD": symbol,
                "TDD_OPNPRC": "266000",
                "TDD_HGPRC": "266500",
                "TDD_LWPRC": "247000",
                "TDD_CLSPRC": "249500",
                "ACC_TRDVOL": "26175580",
            }
        )

    rows, metadata = mod._fetch_krx_daily(
        "2026-07-24",
        auth_key="secret-auth-key",
        get=fake_get,
    )

    assert [url.rsplit("/", 1)[-1] for url, _kwargs in calls] == [
        "stk_bydd_trd",
        "ksq_bydd_trd",
    ]
    assert all(call[1]["params"] == {"basDd": "20260724"} for call in calls)
    assert all(call[1]["headers"]["AUTH_KEY"] == "secret-auth-key" for call in calls)
    assert rows["005930"] == {
        "open": 266000,
        "high": 266500,
        "low": 247000,
        "close": 249500,
        "volume": 26175580,
        "raw": {
            "BAS_DD": "20260724",
            "ISU_CD": "005930",
            "TDD_OPNPRC": "266000",
            "TDD_HGPRC": "266500",
            "TDD_LWPRC": "247000",
            "TDD_CLSPRC": "249500",
            "ACC_TRDVOL": "26175580",
        },
    }
    serialized_metadata = json.dumps(metadata, ensure_ascii=False)
    assert "secret-auth-key" not in serialized_metadata
    assert metadata["status"] == "pass"
    assert metadata["auth_configured"] is True
    assert metadata["auth_value_recorded"] is False
    assert metadata["legacy_mdc_endpoint_called"] is False


def test_krx_open_api_rejects_http_200_error_or_wrong_date_payload():
    class Response:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    payloads = iter(
        [
            {"result_code": "AUTH_ERROR"},
            {
                "OutBlock_1": [
                    {
                        "BAS_DD": "20260723",
                        "ISU_CD": "100090",
                    }
                ]
            },
        ]
    )

    rows, metadata = mod._fetch_krx_daily(
        "2026-07-24",
        auth_key="secret-auth-key",
        get=lambda *args, **kwargs: Response(next(payloads)),
    )

    assert rows == {}
    assert metadata["status"] == "source_unavailable"
    assert metadata["error"] == "krx_open_api_endpoint_failure"
    assert metadata["response_sha256"] is None
    assert set(metadata["endpoint_errors"]) == {
        "stk_bydd_trd",
        "ksq_bydd_trd",
    }
    assert "secret-auth-key" not in json.dumps(metadata)


def test_krx_open_api_marks_all_unauthorized_endpoints_explicitly():
    class Response:
        status_code = 401

        def raise_for_status(self):
            error = requests.HTTPError("401 Client Error: Unauthorized")
            error.response = self
            raise error

    rows, metadata = mod._fetch_krx_daily(
        "2026-07-24",
        auth_key="secret-auth-key",
        get=lambda *args, **kwargs: Response(),
    )

    assert rows == {}
    assert metadata["status"] == "source_unavailable"
    assert metadata["error"] == "krx_open_api_unauthorized"
    assert metadata["endpoint_http_statuses"] == {
        "stk_bydd_trd": 401,
        "ksq_bydd_trd": 401,
    }
    assert "secret-auth-key" not in json.dumps(metadata)


def test_exact_payload_validation_reads_entry_and_holding_bars():
    entry_row = {
        "request_id": "entry-1",
        "payload_sha256": "a" * 64,
        "endpoint": "entry_price",
        "redacted": False,
        "replay_exact": True,
        "sanitized_user_input": {
            "stock_code": "100090",
            "entry_candle_context": {
                "venue": "KRX",
                "session": "krx_regular",
                "request_code": "100090",
                "bars": [
                    {
                        "t": "10:00",
                        "o": 100,
                        "h": 102,
                        "l": 99,
                        "c": 101,
                        "v": 10,
                        "forming": False,
                        "partial_volume": False,
                    },
                    {
                        "t": "10:01",
                        "o": 101,
                        "h": 103,
                        "l": 100,
                        "c": 102,
                        "v": 99,
                        "forming": True,
                        "partial_volume": True,
                    },
                ],
            },
        },
        "_response_provenance": {
            "provider_actual": "bedrock",
            "payload_replay_exact": True,
            "request_capture_status": "captured",
            "response_sha256": "c" * 64,
        },
    }
    holding_row = {
        "request_id": "holding-1",
        "payload_sha256": "b" * 64,
        "endpoint": "holding_score",
        "redacted": False,
        "replay_exact": True,
        "sanitized_user_input": {
            "stock_code": "100090",
            "holding_decision_context": {
                "venue": "KRX",
                "session": "krx_regular",
                "request_code": "100090",
                "candle": {
                    "bars": [
                        {
                            "minute": "10:00",
                            "open": 100,
                            "high": 102,
                            "low": 99,
                            "close": 101,
                            "volume": 10,
                            "is_forming": False,
                            "volume_is_partial": False,
                        }
                    ]
                },
            },
        },
        "_response_provenance": {
            "provider_actual": "openai",
            "payload_replay_exact": True,
            "request_capture_status": "captured",
            "response_sha256": "d" * 64,
        },
    }

    result = mod.build_exact_payload_comparisons(
        payload_rows=[entry_row, holding_row],
        route_minutes={
            "100090": [
                {
                    "source_timestamp": "20260724100000",
                    "시가": 100,
                    "고가": 102,
                    "저가": 99,
                    "현재가": 101,
                    "거래량": 10,
                }
            ]
        },
        target_date="2026-07-24",
    )

    assert result["summary"] == {
        "request_count": 2,
        "observed_request_count": 2,
        "valid_exact_request_count": 2,
        "endpoint_counts": {"entry_price": 1, "holding_score": 1},
        "observed_endpoint_counts": {"entry_price": 1, "holding_score": 1},
        "comparable_field_count": 10,
        "match_count": 10,
        "mismatch_count": 0,
        "source_unavailable_count": 0,
        "forming_bar_excluded_count": 1,
        "forming_bar_included_count": 0,
        "provider_none_count": 0,
        "non_exact_payload_count": 0,
        "request_capture_missing_count": 0,
        "response_hash_missing_count": 0,
        "required_payload_match_status": "pass",
    }


def test_exact_payload_validation_rejects_redacted_or_uncaptured_rows():
    payload = {
        "request_id": "entry-redacted",
        "payload_sha256": "e" * 64,
        "endpoint": "entry_price",
        "redacted": True,
        "replay_exact": False,
        "sanitized_user_input": {
            "stock_code": "100090",
            "entry_candle_context": {
                "venue": "KRX",
                "session": "krx_regular",
                "request_code": "100090",
                "bars": [
                    {
                        "t": "10:00",
                        "o": 100,
                        "h": 102,
                        "l": 99,
                        "c": 101,
                        "v": 10,
                        "forming": False,
                        "partial_volume": False,
                    }
                ],
            },
        },
        "_response_provenance": {
            "provider_actual": "openai",
            "payload_replay_exact": False,
            "request_capture_status": "missing",
            "response_sha256": None,
        },
    }

    result = mod.build_exact_payload_comparisons(
        payload_rows=[payload],
        route_minutes={"100090": []},
        target_date="2026-07-24",
    )

    assert result["summary"]["observed_request_count"] == 1
    assert result["summary"]["valid_exact_request_count"] == 0
    assert result["summary"]["non_exact_payload_count"] == 1
    assert result["summary"]["request_capture_missing_count"] == 1
    assert result["summary"]["response_hash_missing_count"] == 1
    assert result["summary"]["required_payload_match_status"] == "fail"


def test_payload_provenance_falls_back_to_unique_payload_hash(tmp_path, monkeypatch):
    trace_dir = tmp_path / "traces"
    trace_dir.mkdir()
    monkeypatch.setattr(mod, "TRACE_DIR", trace_dir)
    payload_hash = "c" * 64
    (trace_dir / "ai_decision_trace_2026-07-24.jsonl").write_text(
        json.dumps(
            {
                "decision_trace_id": "legacy-trace",
                "payload_sha256": payload_hash,
                "provider_actual": "openai",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    enriched = mod.enrich_payloads_with_response_provenance(
        "2026-07-24",
        {
            "005930": [
                {
                    "payload_sha256": payload_hash,
                    "sanitized_user_input": {"stock_code": "005930"},
                }
            ]
        },
    )

    assert enriched["005930"][0]["_response_provenance"]["provider_actual"] == "openai"


def test_naver_daily_fallback_volume_is_not_strictly_compared():
    result = mod.build_symbol_comparison(
        symbol="100090",
        venue="KRX",
        target_date="2026-07-24",
        kiwoom_daily={
            "open": 16940,
            "high": 20850,
            "low": 16330,
            "close": 18350,
            "volume": 20219380,
        },
        kiwoom_minutes=[],
        external_daily={
            "open": 16940,
            "high": 20850,
            "low": 16330,
            "close": 18350,
            "volume": 20117530,
        },
        naver_minutes=[],
        ai_payload_row=None,
        source_meta={
            "daily_external_source": "NAVER_FCHART_DAILY",
            "daily_external_comparable_fields": (
                "open",
                "high",
                "low",
                "close",
            ),
        },
    )

    volume = next(
        row for row in result["comparison_rows"] if row["field"] == "daily.volume"
    )
    assert volume["status"] == "NOT_COMPARABLE"
    assert volume["reason"] == "naver_daily_volume_snapshot_not_final_krx_basis"


def test_krx_daily_empty_outblock_is_non_blocking_intraday_observation():
    observation = mod._krx_daily_verification_observation(
        {
            "status": "source_unavailable",
            "error": "krx_open_api_endpoint_failure",
        }
    )

    assert observation == {
        "source": "KRX_OPEN_API_STOCK_DAILY",
        "availability_status": "source_unavailable",
        "error": "krx_open_api_endpoint_failure",
        "verification_role": "non_blocking_external_daily_observation",
        "required_source_match_gate": False,
        "runtime_promotion_gate": False,
        "reason": (
            "krx_open_api_daily_response_not_a_completed_intraday_validation_basis"
        ),
    }


def test_live_report_uses_explicit_market_request_code_for_krx_and_nxt(
    monkeypatch,
):
    from src.utils import kiwoom_utils

    calls = []

    class DailyFrame:
        empty = False

        def iterrows(self):
            yield datetime(2026, 7, 24), {
                "Open": 1,
                "High": 1,
                "Low": 1,
                "Close": 1,
                "Volume": 1,
            }

    monkeypatch.setattr(kiwoom_utils, "get_kiwoom_token", lambda: "token")
    monkeypatch.setattr(
        kiwoom_utils,
        "get_daily_data_ka10005_df",
        lambda token, symbol: DailyFrame(),
    )

    def minute_rows(token, symbol, limit, explicit_request_code):
        calls.append((symbol, explicit_request_code))
        return [], {"request_code": symbol}

    monkeypatch.setattr(
        kiwoom_utils,
        "get_minute_candles_ka10080_with_meta",
        minute_rows,
    )
    monkeypatch.setattr(
        mod,
        "_fetch_krx_daily",
        lambda target_date: (
            {
                "005930": {
                    "open": 1,
                    "high": 1,
                    "low": 1,
                    "close": 1,
                    "volume": 1,
                }
            },
            {},
        ),
    )
    monkeypatch.setattr(
        mod,
        "_fetch_naver_chart",
        lambda symbol, timeframe, count: ([], {}),
    )
    payload_dates = []
    request_dates = []

    def load_payloads(target_date):
        payload_dates.append(target_date)
        return {}

    def load_requests(target_date):
        request_dates.append(target_date)
        return {}

    monkeypatch.setattr(mod, "load_ai_payloads", load_payloads)
    monkeypatch.setattr(mod, "load_request_provenance", load_requests)

    report = mod.build_live_report(
        "2026-07-24",
        ["005930", "005930_NX"],
        provenance_date="2026-07-26",
    )

    assert calls == [("005930", True), ("005930_NX", True)]
    assert payload_dates == ["2026-07-26"]
    assert request_dates == ["2026-07-26"]
    assert report["date"] == "2026-07-24"
    assert report["provenance_capture_date"] == "2026-07-26"
    assert (
        report["external_source_policy"][
            "krx_open_api_daily_required_source_match_gate"
        ]
        is False
    )
    assert (
        report["external_source_policy"]["krx_open_api_daily_runtime_promotion_gate"]
        is False
    )
    assert (
        report["provenance_join_policy"]
        == "explicit_forensic_replay_market_date_to_capture_date"
    )


def test_live_report_rejects_provenance_date_before_market_date():
    with pytest.raises(
        ValueError,
        match="provenance capture date cannot precede",
    ):
        mod.build_live_report(
            "2026-07-24",
            ["005930"],
            provenance_date="2026-07-23",
        )
