from __future__ import annotations

import json
import hashlib
from datetime import date

import pytest

from src.engine.monitoring import pure_market_kiwoom_backfill as backfill


class _Response:
    def __init__(self, payload, *, headers=None, status_code=200):
        self._payload = payload
        self.headers = headers or {}
        self.status_code = status_code

    def json(self):
        return self._payload


def _row(timestamp: str, price: int = 100_000) -> dict[str, str]:
    return {
        "cntr_tm": timestamp,
        "open_pric": str(price),
        "high_pric": str(price + 100),
        "low_pric": str(price - 100),
        "cur_prc": str(price + 50),
        "trde_qty": "1234",
    }


def test_backfill_uses_official_fields_and_continuation_without_auth_mutation():
    calls = []
    responses = iter(
        [
            _Response(
                {"return_code": 0, "stk_min_pole_chart_qry": [_row("20260608100000")]},
                headers={"cont-yn": "Y", "next-key": "page-2"},
            ),
            _Response(
                {
                    "return_code": 0,
                    "stk_min_pole_chart_qry": [
                        _row("20260605090000"),
                        _row("20260604152900"),
                    ],
                },
                headers={"cont-yn": "N"},
            ),
        ]
    )

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return next(responses)

    bars, meta = backfill.fetch_ka10080_history(
        token="shared-token",
        venue="KRX",
        start_date=date(2026, 6, 5),
        end_date=date(2026, 6, 8),
        page_delay_sec=0,
        post=post,
    )

    assert [bar.source_timestamp for bar in bars] == [
        "20260605090000",
        "20260608100000",
    ]
    assert calls[0][1]["json"] == {
        "stk_cd": "005930",
        "tic_scope": "1",
        "upd_stkpc_tp": "1",
    }
    assert calls[1][1]["headers"]["cont-yn"] == "Y"
    assert calls[1][1]["headers"]["next-key"] == "page-2"
    assert calls[0][1]["headers"]["authorization"] == "Bearer shared-token"
    assert meta["source_quality_status"] == "PASS"
    assert meta["start_date_fully_bracketed"] is True


def test_backfill_preserves_nxt_route_and_filters_session_gaps():
    def post(_url, **kwargs):
        assert kwargs["json"]["stk_cd"] == "005930_NX"
        return _Response(
            {
                "return_code": 0,
                "stk_min_pole_chart_qry": [
                    _row("20260605080500"),
                    _row("20260605085500"),
                    _row("20260605160000"),
                ],
            }
        )

    bars, meta = backfill.fetch_ka10080_history(
        token="token",
        venue="NXT",
        start_date=date(2026, 6, 5),
        end_date=date(2026, 6, 5),
        page_delay_sec=0,
        post=post,
    )

    assert [(bar.session, bar.source_timestamp) for bar in bars] == [
        ("NXT_PREMARKET", "20260605080500"),
        ("NXT_AFTERMARKET", "20260605160000"),
    ]
    assert meta["invalid_row_count"] == 0
    assert meta["out_of_session_row_count"] == 1
    assert meta["start_date_fully_bracketed"] is False
    assert meta["source_quality_status"] == "PARTIAL"


def test_backfill_auth_failure_is_fail_closed_without_retry():
    call_count = 0

    def post(_url, **_kwargs):
        nonlocal call_count
        call_count += 1
        return _Response({"return_code": 8005})

    with pytest.raises(backfill.BackfillError, match="ka10080_return_8005"):
        backfill.fetch_ka10080_history(
            token="expired",
            venue="KRX",
            start_date=date(2026, 6, 5),
            end_date=date(2026, 6, 5),
            post=post,
        )
    assert call_count == 1


def test_kospi_backfill_uses_official_ka20005_contract_and_raw_x100_prices():
    calls = []
    responses = iter(
        [
            _Response(
                {
                    "return_code": 0,
                    "inds_min_pole_qry": [_row("20260605090000", 300_000)],
                },
                headers={"cont-yn": "Y", "next-key": "older"},
            ),
            _Response(
                {
                    "return_code": 0,
                    "inds_min_pole_qry": [_row("20260604152900", 299_000)],
                },
            ),
        ]
    )

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return next(responses)

    bars, meta = backfill.fetch_ka20005_history(
        token="shared-token",
        start_date=date(2026, 6, 5),
        end_date=date(2026, 6, 5),
        page_delay_sec=0,
        post=post,
    )

    assert calls[0][1]["headers"]["api-id"] == "ka20005"
    assert calls[0][1]["json"] == {"inds_cd": "001", "tic_scope": "1"}
    assert len(bars) == 1
    assert bars[0].symbol == "KOSPI"
    assert bars[0].close == 300_050
    assert bars[0].price_scale == "raw_index_x100"
    assert meta["source_quality_status"] == "PASS"


def test_backfill_shared_read_control_is_source_only_and_persisted_in_meta(
    monkeypatch,
):
    admissions = []
    request_headers = []

    class Admission:
        admitted = True
        reason = "shared_read_rate_admitted"

        @staticmethod
        def as_dict():
            return {"admitted": True, "scope_digest": "digest"}

    monkeypatch.setattr(
        backfill.kiwoom_utils,
        "acquire_kiwoom_read_capacity",
        lambda **kwargs: admissions.append(kwargs) or Admission(),
    )
    monkeypatch.setattr(
        backfill.kiwoom_utils,
        "resolve_kiwoom_request_token",
        lambda _token: "HANDOFF_TOKEN",
    )

    def post(_url, **kwargs):
        request_headers.append(kwargs["headers"])
        return _Response(
            {
                "return_code": 0,
                "stk_min_pole_chart_qry": [_row("20260604152900")],
            }
        )

    bars, meta = backfill.fetch_ka10080_history(
        token="shared-token",
        venue="KRX",
        start_date=date(2026, 6, 5),
        end_date=date(2026, 6, 5),
        post=post,
        shared_read_control_enabled=True,
    )

    assert bars == []
    assert admissions[0]["api_id"] == "ka10080"
    assert admissions[0]["request_class"] == "source_only"
    assert admissions[0]["token"] == "HANDOFF_TOKEN"
    assert request_headers[0]["authorization"] == "Bearer HANDOFF_TOKEN"
    assert meta["shared_read_control_enabled"] is True
    assert meta["shared_read_control_last_admission"]["scope_digest"] == "digest"


def test_backfill_http_429_publishes_shared_cooldown(monkeypatch):
    rate_limits = []

    class Admission:
        admitted = True
        reason = "shared_read_rate_admitted"

        @staticmethod
        def as_dict():
            return {"admitted": True}

    monkeypatch.setattr(
        backfill.kiwoom_utils,
        "acquire_kiwoom_read_capacity",
        lambda **_kwargs: Admission(),
    )
    monkeypatch.setattr(
        backfill.kiwoom_utils,
        "record_kiwoom_read_rate_limit",
        lambda **kwargs: rate_limits.append(kwargs) or {"recorded": True},
    )

    with pytest.raises(backfill.BackfillError, match="ka20005_http_429"):
        backfill.fetch_ka20005_history(
            token="shared-token",
            start_date=date(2026, 6, 5),
            end_date=date(2026, 6, 5),
            post=lambda *_args, **_kwargs: _Response({}, status_code=429),
            shared_read_control_enabled=True,
        )

    assert rate_limits[0]["api_id"] == "ka20005"
    assert rate_limits[0]["http_status_code"] == 429


def test_backfill_manifest_marks_partial_source(tmp_path):
    paths = backfill.write_backfill(
        [],
        start_date=date(2026, 6, 5),
        end_date=date(2026, 6, 5),
        venue_meta=[{"venue": "KRX", "source_quality_status": "PARTIAL"}],
        output_dir=tmp_path,
    )
    manifest = json.loads(paths[1].read_text(encoding="utf-8"))
    assert manifest["source_quality_status"] == "PARTIAL"
    assert manifest["runtime_effect"] is False
    assert manifest["token_mutation_forbidden"] is True
    assert manifest["data_sha256"] == hashlib.sha256(paths[0].read_bytes()).hexdigest()
