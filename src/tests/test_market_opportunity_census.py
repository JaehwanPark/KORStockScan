from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from src.engine.monitoring import market_opportunity_census as census
from src.utils import kiwoom_utils


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_ka10027_forwards_official_venue_and_filter_contract(monkeypatch):
    captured = {}

    def fake_fetch(**kwargs):
        captured.update(kwargs)
        return [
            {
                "pred_pre_flu_rt_upper": [
                    {
                        "stk_cd": "005930_KS",
                        "stk_nm": "삼성전자",
                        "cur_prc": "+249500",
                        "flu_rt": "+3.25",
                        "now_trde_qty": "26175580",
                        "cntr_str": "112.5",
                        "pred_pre_sig": "2",
                    }
                ]
            }
        ]

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", fake_fetch)

    rows = kiwoom_utils.get_top_fluctuation_ka10027(
        "token",
        trde_qty_cnd="0010",
        limit=10,
        stex_tp="1",
        stk_cnd="4",
        pric_cnd="8",
        trde_prica_cnd="10",
    )

    assert captured["api_id"] == "ka10027"
    assert captured["payload"]["stex_tp"] == "1"
    assert captured["payload"]["stk_cnd"] == "4"
    assert captured["payload"]["pric_cnd"] == "8"
    assert captured["payload"]["trde_prica_cnd"] == "10"
    assert captured["use_continuous"] is True
    assert captured["max_pages"] == 1
    assert rows == [
        {
            "Code": "005930",
            "Name": "삼성전자",
            "Price": 249500,
            "ChangeRate": 3.25,
            "PreSig": "2",
            "PreSigDirection": "positive",
            "Volume": 26175580,
            "CntrStr": 112.5,
        }
    ]


def test_ka10027_applies_pure_equity_filter_before_output_limit(monkeypatch):
    monkeypatch.setattr(
        kiwoom_utils,
        "fetch_kiwoom_api_continuous",
        lambda **_kwargs: [
            {
                "pred_pre_flu_rt_upper": [
                    {
                        "stk_cd": "069500",
                        "stk_nm": "KODEX 200",
                        "cur_prc": "30000",
                    },
                    {
                        "stk_cd": "0182R0_AL",
                        "stk_nm": "1Q K반도체TOP2+",
                        "cur_prc": "9000",
                    },
                    {
                        "stk_cd": "005930",
                        "stk_nm": "삼성전자",
                        "cur_prc": "70000",
                        "flu_rt": "3.0",
                    },
                ]
            }
        ],
    )

    rows = kiwoom_utils.get_top_fluctuation_ka10027(
        "token", limit=1, pure_equity_only=True
    )

    assert [row["Code"] for row in rows] == ["005930"]
    assert rows[0]["SourceRank"] == 3
    assert rows[0]["PureEquityFilterApplied"] is True


def test_ka10027_flattens_continuous_pages_until_requested_raw_depth(monkeypatch):
    captured = {}

    def fake_fetch(**kwargs):
        captured.update(kwargs)
        return [
            {
                "pred_pre_flu_rt_upper": [
                    {
                        "stk_cd": f"{index * 10:06d}",
                        "stk_nm": f"PAGE1_{index}",
                        "cur_prc": "10000",
                        "flu_rt": f"{30.0 - index * 0.1:.2f}",
                    }
                    for index in range(20)
                ]
            },
            {
                "pred_pre_flu_rt_upper": [
                    {
                        "stk_cd": f"{800000 + index * 10:06d}",
                        "stk_nm": f"PAGE2_{index}",
                        "cur_prc": "10000",
                        "flu_rt": f"{24.9 - index * 0.1:.2f}",
                    }
                    for index in range(20)
                ]
            },
            {
                "pred_pre_flu_rt_upper": [
                    {
                        "stk_cd": f"{900000 + index * 10:06d}",
                        "stk_nm": f"PAGE3_{index}",
                        "cur_prc": "10000",
                        "flu_rt": f"{22.9 - index * 0.1:.2f}",
                    }
                    for index in range(20)
                ]
            },
        ]

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", fake_fetch)

    rows = kiwoom_utils.get_top_fluctuation_ka10027(
        "token",
        limit=60,
        pure_equity_only=True,
    )

    assert captured["use_continuous"] is True
    assert captured["max_pages"] == 3
    assert len(rows) == 60
    assert rows[20]["Code"] == "800000"
    assert rows[20]["SourceRank"] == 21
    assert rows[20]["SourceUniverseSize"] == 60


def test_ka10027_zero_limit_returns_no_rows(monkeypatch):
    monkeypatch.setattr(
        kiwoom_utils,
        "fetch_kiwoom_api_continuous",
        lambda **_kwargs: [
            {
                "pred_pre_flu_rt_upper": [
                    {"stk_cd": "005930", "stk_nm": "삼성전자", "cur_prc": "70000"}
                ]
            }
        ],
    )

    assert kiwoom_utils.get_top_fluctuation_ka10027("token", limit=0) == []


def test_capture_is_sanitized_source_only_and_separates_venues():
    calls = []

    def fake_fetch(token, **kwargs):
        calls.append((token, kwargs))
        return [
            {
                "Code": "005930",
                "Name": "삼성전자",
                "Price": 100000,
                "ChangeRate": 5.0,
                "Volume": 100000,
                "CntrStr": 120.0,
                "PreSig": "2",
            }
        ]

    rows = census.capture_market_snapshots(
        "secret-token",
        target_date="2026-07-30",
        captured_at=datetime.fromisoformat("2026-07-30T10:00:00+09:00"),
        venues=("KRX", "NXT"),
        panels=("liquid_common",),
        fetcher=fake_fetch,
    )

    assert len(rows) == 2
    assert {row["venue"] for row in rows} == {"KRX", "NXT"}
    assert {call[1]["stex_tp"] for call in calls} == {"1", "2"}
    assert all(row["metric_contract"]["runtime_effect"] is False for row in rows)
    assert all(row["source"]["credential_fields_stored"] == [] for row in rows)
    assert "secret-token" not in json.dumps(rows, ensure_ascii=False)


def test_report_splits_forward_exact_from_noncausal_retrospective(tmp_path):
    snapshot_path = tmp_path / "snapshots.jsonl"
    pipeline_path = tmp_path / "pipeline.jsonl"
    ai_path = tmp_path / "ai.jsonl"
    captured_at = "2026-07-30T10:00:00+09:00"
    base_snapshot = {
        "schema_version": census.SCHEMA_VERSION,
        "target_date": "2026-07-30",
        "captured_at": captured_at,
        "panel": "liquid_common",
        "source_quality_status": "ok",
        "rows": [
            {
                "rank": 1,
                "stock_code": "005930",
                "stock_name": "삼성전자",
                "current_price": 100000,
                "change_rate_pct": 5.0,
            }
        ],
    }
    _write_jsonl(
        snapshot_path,
        [
            {**base_snapshot, "venue": "KRX"},
            {**base_snapshot, "venue": "NXT"},
            {
                **base_snapshot,
                "target_date": "2026-07-29",
                "venue": "KRX",
            },
            {
                **base_snapshot,
                "schema_version": "unexpected_schema",
                "venue": "KRX",
            },
        ],
    )
    _write_jsonl(
        pipeline_path,
        [
            {
                "stage": "scalping_scanner_candidate_promoted",
                "stock_code": "005930",
                "emitted_at": "2026-07-30T09:59:00+09:00",
                "fields": {"effective_venue": "KRX_REGULAR"},
            },
            {
                "stage": "scalping_scanner_fast_precheck",
                "stock_code": "005930",
                "emitted_at": "2026-07-30T10:01:00+09:00",
                "fields": {"effective_venue": "KRX_REGULAR"},
            },
            {
                "stage": "scalping_scanner_candidate_promoted",
                "stock_code": "005930",
                "emitted_at": "2026-07-30T10:00:30+09:00",
                "fields": {"effective_venue": "KRX_NXT_INTEGRATED"},
            },
            {
                "stage": "scanner_async_result_commit",
                "stock_code": "005930",
                "emitted_at": "2026-07-30T10:02:00+09:00",
                "fields": {"effective_venue": "KRX_REGULAR"},
            },
        ],
    )
    _write_jsonl(
        ai_path,
        [
            {
                "endpoint": "analyze_target",
                "stock_code": "005930",
                "decision_ts": "2026-07-30T10:03:00+09:00",
                "effective_venue": "NXT_AFTERMARKET",
                "action": "WAIT",
                "provider_called": True,
                "provider_actual": "openai",
            },
            {
                "endpoint": "analyze_target",
                "stock_code": "005930",
                "decision_ts": "2026-07-30T10:04:00+09:00",
                "effective_venue": "KRX_REGULAR",
                "action": "DROP",
                "provider_called": "False",
                "provider_actual": "none",
            },
            {
                "endpoint": "analyze_target",
                "stock_code": "005930",
                "decision_ts": "2026-07-30T10:05:00+09:00",
                "effective_venue": "KRX_REGULAR",
                "action": "WAIT",
                "provider_called": True,
                "provider_actual": "",
            },
        ],
    )

    report = census.build_report(
        "2026-07-30",
        snapshot_path=snapshot_path,
        pipeline_path=pipeline_path,
        ai_trace_path=ai_path,
    )

    views = report["coverage"]["liquid_common"]["top_10"]
    forward = views["forward_exact"]
    venue_retrospective = views["same_day_venue_consistent_retrospective"]
    any_retrospective = views["same_day_any_venue_retrospective_noncausal"]
    assert forward["episode_count"] == 2
    assert forward["stage_counts"]["scanner_promoted"] == 0
    assert forward["stage_counts"]["fast_precheck"] == 1
    assert forward["stage_counts"]["entry_ai_trace"] == 2
    assert forward["stage_counts"]["entry_ai_provider_called"] == 1
    assert venue_retrospective["stage_counts"]["scanner_promoted"] == 1
    assert venue_retrospective["stage_counts"]["entry_ai_trace"] == 2
    assert (
        venue_retrospective["by_venue"]["KRX"]["stage_counts"]["scanner_promoted"] == 1
    )
    assert (
        venue_retrospective["by_venue"]["NXT"]["stage_counts"][
            "entry_ai_provider_called"
        ]
        == 1
    )
    assert any_retrospective["stage_counts"]["scanner_promoted"] == 2
    assert any_retrospective["stage_counts"]["entry_ai_trace"] == 2
    assert report["source_quality"]["foreign_target_date_snapshot_count"] == 1
    assert report["source_quality"]["invalid_contract_snapshot_count"] == 1


def test_guard_block_remains_first_terminal_gap():
    observed_at = datetime.fromisoformat("2026-07-30T10:00:00+09:00")
    row = census._coverage_row(
        {
            "venue": "KRX",
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "first_census_at": observed_at,
        },
        {
            "005930": {
                "scanner_guard_observed": [
                    {
                        "ts": observed_at,
                        "venue": "KRX",
                        "reason": "source_quality_blocked",
                    }
                ]
            }
        },
        after=observed_at,
        require_venue=True,
    )

    assert (
        row["terminal_coverage_reason"]
        == "scanner_source_guard_blocked_before_promotion"
    )


def test_empty_fetch_preserves_source_unavailable_evidence():
    def fake_fetch(*args, **kwargs):
        return []

    rows = census.capture_market_snapshots(
        "token",
        target_date="2026-07-30",
        captured_at=datetime(2026, 7, 30, 9, 5, tzinfo=census.KST),
        venues=("KRX",),
        panels=("all",),
        fetcher=fake_fetch,
    )

    assert rows[0]["source_quality_status"] == "source_unavailable"
    assert rows[0]["row_count"] == 0


def test_capture_rejects_historical_relabeling():
    def fake_fetch(*args, **kwargs):
        return []

    try:
        census.capture_market_snapshots(
            "token",
            target_date="2026-07-29",
            captured_at=datetime.fromisoformat("2026-07-30T10:00:00+09:00"),
            venues=("KRX",),
            panels=("all",),
            fetcher=fake_fetch,
        )
    except ValueError as exc:
        assert "actual capture date" in str(exc)
    else:
        raise AssertionError("historical relabeling must fail")


def test_snapshot_append_and_markdown_forbid_live_authority(tmp_path):
    path = tmp_path / "census.jsonl"
    record = {
        "source_quality_status": "ok",
        "metric_contract": census.METRIC_CONTRACT,
    }

    assert census.append_snapshot_records(path, [record]) == 1
    assert list(census.iter_jsonl(path)) == [record]

    markdown = census.render_markdown(
        {
            "target_date": "2026-07-30",
            "status": "ok",
            "coverage": {},
        }
    )
    assert "runtime_effect: `false`" in markdown
    assert "`standalone_buy`" in markdown
