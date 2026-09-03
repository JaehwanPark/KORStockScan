from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from src.engine.monitoring import market_opportunity_census as census
from src.utils import kiwoom_utils


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _prune_bbo_event(
    when: datetime,
    *,
    bid: int,
    ask: int,
    bid_qty: int = 100,
    ask_qty: int = 100,
) -> dict:
    epoch = when.timestamp()
    return {
        "stage": "scalping_scanner_prune_bbo_observation",
        "stock_code": "005930",
        "emitted_at": when.isoformat(),
        "fields": {
            "observation_schema_version": census.PRUNE_BBO_OBSERVATION_SCHEMA_VERSION,
            "scanner_prune_observer_episode_id": "PRUNEBBO-1",
            "scanner_prune_observer_status": "captured",
            "scanner_prune_observer_source_quality_pass": True,
            "scanner_prune_observer_route_match": True,
            "scanner_prune_observer_price_source": (
                "ka10004_rest_orderbook_exact_request_code"
            ),
            "scanner_prune_observer_request_code": "005930",
            "scanner_prune_observer_response_request_code": "005930",
            "scanner_prune_observer_observed_epoch": epoch,
            "scanner_prune_observer_request_started_epoch": epoch - 0.1,
            "scanner_prune_observer_request_completed_epoch": epoch,
            "scanner_prune_observer_anchor_to_schedule_delay_sec": 0.0,
            "scanner_prune_observer_schedule_lag_sec": 0.0,
            "scanner_prune_observer_scheduled_offset_sec": 0,
            "scanner_prune_observer_quote_age_ms": 0.0,
            "scanner_prune_observer_best_bid": bid,
            "scanner_prune_observer_best_ask": ask,
            "scanner_prune_observer_best_bid_qty": bid_qty,
            "scanner_prune_observer_best_ask_qty": ask_qty,
            "effective_venue": "KRX",
            "venue": "KRX",
            "market_session_bucket": "krx_regular",
            "scanner_prune_observer_expected_observed_venue": "KRX",
            "decision_authority": "scanner_prune_bbo_observation_only",
            "actual_order_submitted": False,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "broker_order_forbidden": True,
            "market_data_request_effect": True,
        },
    }


def _promoted_ws_bundle_event(when: datetime) -> dict:
    samples = [
        {
            "observed_epoch": when.timestamp(),
            "recorded_epoch": when.timestamp(),
            "best_bid": 999,
            "best_ask": 1000,
            "best_bid_qty": 100,
            "best_ask_qty": 100,
            "quote_age_ms": 0.0,
            "source_provenance": "existing_ws_route_scoped_0d_snapshot",
            "effective_venue": "KRX",
            "market_session_bucket": "krx_regular",
            "observed_venue": "KRX",
            "route_scope_status": "exact_0d_route_snapshot",
            "market_route": "krx_regular",
            "observed_item": "005930",
            "scanner_promotion_id": "PROM-1",
        }
    ]
    return {
        "stage": "rising_missed_entry_turn_pre_anchor_bbo_path",
        "stock_code": "005930",
        "emitted_at": (when + timedelta(seconds=1)).isoformat(),
        "fields": {
            "effective_venue": "KRX",
            "market_session_bucket": "krx_regular",
            "scanner_promotion_id": "PROM-1",
            "rising_missed_tp1_evaluation_id": "EVAL-1",
            "rising_missed_entry_turn_bbo_bundle_schema_version": (
                census.PRE_ANCHOR_BUNDLE_SCHEMA_VERSION
            ),
            "rising_missed_entry_turn_bbo_sample_count": len(samples),
            "rising_missed_entry_turn_bbo_samples": json.dumps(samples, sort_keys=True),
            "decision_authority": (
                "entry_turn_pre_anchor_existing_ws_bbo_observation_only"
            ),
            "actual_order_submitted": False,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "broker_order_forbidden": True,
        },
    }


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
                    },
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
    assert all(
        len(row["source"]["normalized_source_payload_sha256"]) == 64 for row in rows
    )
    assert all(
        row["source"]["source_hash_scope"]
        == "sanitized_request_contract_plus_normalized_response_rows"
        for row in rows
    )
    assert {row["session"] for row in rows} == {
        "KRX_REGULAR",
        "NXT_REGULAR_OVERLAP",
    }
    assert "secret-token" not in json.dumps(rows, ensure_ascii=False)


def test_capture_collects_bounded_exact_route_external_bbo():
    captured_at = datetime.fromisoformat("2026-07-30T10:00:00+09:00")
    bbo_calls = []

    def fake_gainers(_token, **_kwargs):
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

    def fake_bbo(token, code, **kwargs):
        bbo_calls.append((token, code, kwargs))
        return {
            "source": "ka10004_rest_orderbook",
            "stock_code": "005930",
            "request_code": "005930_NX",
            "explicit_request_code": True,
            "rest_received_ts": captured_at.timestamp() + 0.1,
            "best_bid": 99900,
            "best_ask": 100000,
            "best_bid_qty": 12,
            "best_ask_qty": 10,
        }

    clock_values = iter([captured_at.timestamp(), captured_at.timestamp() + 0.2])
    records = census.capture_market_snapshots(
        "secret-token",
        target_date="2026-07-30",
        captured_at=captured_at,
        venues=("NXT",),
        panels=("liquid_common",),
        fetcher=fake_gainers,
        collect_executable_bbo=True,
        bbo_fetcher=fake_bbo,
        bbo_request_reserver=lambda: {
            "status": "reserved",
            "reserved": True,
            "attempt_ordinal": 1,
            "daily_request_cap": census.EXTERNAL_BBO_MAX_REQUESTS_PER_KST_DATE,
        },
        clock=lambda: next(clock_values),
    )

    observation = records[0]["rows"][0]["executable_bbo_observation"]
    assert bbo_calls == [
        (
            "secret-token",
            "005930_NX",
            {"explicit_request_code": True, "max_retries": 1},
        )
    ]
    assert observation["status"] == "captured"
    assert observation["best_bid_qty"] == 12
    assert observation["best_ask_qty"] == 10
    assert observation["market_data_request_effect"] is True
    assert observation["runtime_effect"] is False
    assert observation["actual_order_submitted"] is False
    assert "secret-token" not in json.dumps(records, ensure_ascii=False)
    assert census._snapshot_contract_error(records[0], target_date="2026-07-30") == ""


def test_external_bbo_per_run_budget_records_gap_without_request():
    records = census.capture_market_snapshots(
        "token",
        target_date="2026-07-30",
        captured_at=datetime.fromisoformat("2026-07-30T10:00:00+09:00"),
        venues=("KRX",),
        panels=("liquid_common",),
        fetcher=lambda *_args, **_kwargs: [
            {"Code": "005930", "Name": "삼성전자", "Price": 100000}
        ],
        collect_executable_bbo=True,
        bbo_fetcher=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("BBO request must not run after budget exhaustion")
        ),
        max_bbo_requests_per_run=0,
    )

    observation = records[0]["rows"][0]["executable_bbo_observation"]
    assert observation["request_attempted"] is False
    assert observation["gap_reason"] == "per_run_bbo_request_budget_exhausted"


def test_external_bbo_without_daily_reservation_never_calls_kiwoom():
    records = census.capture_market_snapshots(
        "token",
        target_date="2026-07-30",
        captured_at=datetime.fromisoformat("2026-07-30T10:00:00+09:00"),
        venues=("KRX",),
        panels=("liquid_common",),
        fetcher=lambda *_args, **_kwargs: [
            {"Code": "005930", "Name": "삼성전자", "Price": 100000}
        ],
        collect_executable_bbo=True,
        bbo_fetcher=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("BBO request requires a durable reservation")
        ),
        max_bbo_requests_per_run=1,
    )

    observation = records[0]["rows"][0]["executable_bbo_observation"]
    assert observation["request_attempted"] is False
    assert observation["gap_reason"] == ("daily_bbo_budget_reservation_not_configured")


def test_external_bbo_daily_budget_reservation_is_durable_and_fail_closed(tmp_path):
    path = tmp_path / "budget.json"

    first = census._reserve_external_bbo_request(
        path,
        target_date="2026-09-02",
        limit=41,
        initial_reserved_count=40,
    )
    second = census._reserve_external_bbo_request(
        path,
        target_date="2026-09-02",
        limit=41,
        initial_reserved_count=40,
    )

    assert first["status"] == "reserved"
    assert first["attempt_ordinal"] == 41
    assert second["status"] == "daily_request_cap_exhausted"
    assert second["reserved"] is False
    persisted = json.loads(path.read_text(encoding="utf-8"))
    assert persisted["reserved_request_count"] == 41
    assert persisted["actual_order_submitted"] is False
    assert persisted["market_data_request_effect"] is True


def test_external_bbo_budget_rejects_fractional_persisted_count(tmp_path):
    path = tmp_path / "budget.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": census.EXTERNAL_BBO_BUDGET_SCHEMA_VERSION,
                "target_date": "2026-09-02",
                "reserved_request_count": 1.5,
                "daily_request_cap": census.EXTERNAL_BBO_MAX_REQUESTS_PER_KST_DATE,
                "market_data_request_effect": True,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            }
        ),
        encoding="utf-8",
    )

    reservation = census._reserve_external_bbo_request(
        path,
        target_date="2026-09-02",
    )
    contract = census._load_external_bbo_budget_contract(
        path,
        target_date="2026-09-02",
        minimum_reserved_count=0,
    )

    assert reservation["status"] == "ledger_contract_mismatch"
    assert reservation["reserved"] is False
    assert contract["status"] == "invalid"
    assert contract["reserved_request_count"] is None


def test_external_bbo_budget_contract_binds_snapshot_ordinal(tmp_path):
    path = tmp_path / "budget.json"
    reservation = census._reserve_external_bbo_request(
        path,
        target_date="2026-09-02",
        initial_reserved_count=40,
    )

    contract = census._load_external_bbo_budget_contract(
        path,
        target_date="2026-09-02",
        minimum_reserved_count=41,
    )
    ahead_of_ledger = census._load_external_bbo_budget_contract(
        path,
        target_date="2026-09-02",
        minimum_reserved_count=42,
    )

    assert reservation["attempt_ordinal"] == 41
    assert contract["status"] == "verified"
    assert contract["reserved_request_count"] == 41
    assert ahead_of_ledger["status"] == "invalid"


def test_external_bbo_failed_capture_still_binds_its_budget_reservation():
    observation = {
        "status": "source_quality_gap",
        "request_attempted": True,
        "daily_budget_reservation": {
            "status": "reserved",
            "reserved": True,
            "attempt_ordinal": 7,
            "daily_request_cap": census.EXTERNAL_BBO_MAX_REQUESTS_PER_KST_DATE,
        },
    }

    assert census._external_bbo_reservation_ordinal(observation) == 7


def test_invalid_snapshot_reservation_cannot_reflect_budget_contract(tmp_path):
    captured_at = datetime.fromisoformat("2026-09-02T10:00:00+09:00")
    clock_values = iter([captured_at.timestamp(), captured_at.timestamp() + 0.2])
    records = census.capture_market_snapshots(
        "token",
        target_date="2026-09-02",
        captured_at=captured_at,
        venues=("KRX",),
        panels=("liquid_common",),
        fetcher=lambda *_args, **_kwargs: [
            {"Code": "005930", "Name": "삼성전자", "Price": 100000}
        ],
        collect_executable_bbo=True,
        bbo_fetcher=lambda *_args, **_kwargs: {
            "source": "ka10004_rest_orderbook",
            "stock_code": "005930",
            "request_code": "005930",
            "explicit_request_code": True,
            "rest_received_ts": captured_at.timestamp() + 0.1,
            "best_bid": 99900,
            "best_ask": 100000,
            "best_bid_qty": 12,
            "best_ask_qty": 10,
        },
        bbo_request_reserver=lambda: {
            "status": "reserved",
            "reserved": True,
            "attempt_ordinal": 0,
            "daily_request_cap": census.EXTERNAL_BBO_MAX_REQUESTS_PER_KST_DATE,
        },
        clock=lambda: next(clock_values),
    )
    snapshot_path = tmp_path / "snapshots.jsonl"
    pipeline_path = tmp_path / "pipeline.jsonl"
    ai_path = tmp_path / "ai.jsonl"
    budget_path = tmp_path / "budget.json"
    _write_jsonl(snapshot_path, records)
    _write_jsonl(pipeline_path, [])
    _write_jsonl(ai_path, [])
    budget_path.write_text(
        json.dumps(
            {
                "schema_version": census.EXTERNAL_BBO_BUDGET_SCHEMA_VERSION,
                "target_date": "2026-09-02",
                "reserved_request_count": 1,
                "daily_request_cap": census.EXTERNAL_BBO_MAX_REQUESTS_PER_KST_DATE,
                "market_data_request_effect": True,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            }
        ),
        encoding="utf-8",
    )

    report = census.build_report(
        "2026-09-02",
        snapshot_path=snapshot_path,
        pipeline_path=pipeline_path,
        ai_trace_path=ai_path,
        symbol_master_path=tmp_path / "missing-master.json",
        trigger_receipt_path=tmp_path / "missing-trigger.json",
        external_bbo_budget_path=budget_path,
    )

    source = report["source_quality"]["ex_post_bbo_source"]
    assert source["external_census_capture_contract_reflected"] is False
    assert source["external_census_request_attempted_count"] == 1
    assert source["external_census_reserved_contract_row_count"] == 0
    assert source["external_census_invalid_reservation_attempt_count"] == 1
    assert source["external_census_reservation_accounted_count"] == 1
    assert source["external_census_reservation_conservation_delta"] == 0
    assert source["external_census_reservation_conservation_status"] == "pass"
    assert source["gap_reason_counts"] == {
        "external_census_daily_budget_reservation_invalid": 1
    }


def test_duplicate_snapshot_reservation_ordinal_fails_capture_contract(tmp_path):
    captured_at = datetime.fromisoformat("2026-09-02T10:00:00+09:00")
    clock_values = iter([captured_at.timestamp(), captured_at.timestamp() + 0.2])
    records = census.capture_market_snapshots(
        "token",
        target_date="2026-09-02",
        captured_at=captured_at,
        venues=("KRX",),
        panels=("liquid_common",),
        fetcher=lambda *_args, **_kwargs: [
            {"Code": "005930", "Name": "삼성전자", "Price": 100000}
        ],
        collect_executable_bbo=True,
        bbo_fetcher=lambda *_args, **_kwargs: {
            "source": "ka10004_rest_orderbook",
            "stock_code": "005930",
            "request_code": "005930",
            "explicit_request_code": True,
            "rest_received_ts": captured_at.timestamp() + 0.1,
            "best_bid": 99900,
            "best_ask": 100000,
            "best_bid_qty": 12,
            "best_ask_qty": 10,
        },
        bbo_request_reserver=lambda: {
            "status": "reserved",
            "reserved": True,
            "attempt_ordinal": 1,
            "daily_request_cap": census.EXTERNAL_BBO_MAX_REQUESTS_PER_KST_DATE,
        },
        clock=lambda: next(clock_values),
    )
    snapshot_path = tmp_path / "snapshots.jsonl"
    pipeline_path = tmp_path / "pipeline.jsonl"
    ai_path = tmp_path / "ai.jsonl"
    budget_path = tmp_path / "budget.json"
    _write_jsonl(snapshot_path, [*records, *records])
    _write_jsonl(pipeline_path, [])
    _write_jsonl(ai_path, [])
    budget_path.write_text(
        json.dumps(
            {
                "schema_version": census.EXTERNAL_BBO_BUDGET_SCHEMA_VERSION,
                "target_date": "2026-09-02",
                "reserved_request_count": 1,
                "daily_request_cap": census.EXTERNAL_BBO_MAX_REQUESTS_PER_KST_DATE,
                "market_data_request_effect": True,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            }
        ),
        encoding="utf-8",
    )

    report = census.build_report(
        "2026-09-02",
        snapshot_path=snapshot_path,
        pipeline_path=pipeline_path,
        ai_trace_path=ai_path,
        symbol_master_path=tmp_path / "missing-master.json",
        trigger_receipt_path=tmp_path / "missing-trigger.json",
        external_bbo_budget_path=budget_path,
    )

    source = report["source_quality"]["ex_post_bbo_source"]
    assert source["external_census_request_attempted_count"] == 2
    assert source["external_census_reserved_contract_row_count"] == 2
    assert source["external_census_unique_reserved_ordinal_count"] == 1
    assert source["external_census_duplicate_reserved_ordinal_count"] == 1
    assert source["external_census_reservation_conservation_delta"] == 0
    assert source["external_census_reservation_conservation_status"] == "fail"
    assert source["external_census_capture_contract_reflected"] is False
    assert source["gap_reason_counts"][
        "external_census_daily_budget_reservation_ordinal_duplicate"
    ] == 1


def test_snapshot_source_hash_detects_normalized_row_tampering():
    records = census.capture_market_snapshots(
        "secret-token",
        target_date="2026-07-30",
        captured_at=datetime.fromisoformat("2026-07-30T10:00:00+09:00"),
        venues=("KRX",),
        panels=("liquid_common",),
        fetcher=lambda *_args, **_kwargs: [
            {
                "Code": "005930",
                "Name": "삼성전자",
                "Price": 100000,
                "ChangeRate": 5.0,
                "Volume": 100000,
                "CntrStr": 120.0,
                "PreSig": "2",
            }
        ],
    )

    assert census._snapshot_contract_error(records[0], target_date="2026-07-30") == ""
    records[0]["rows"][0]["current_price"] = 100001
    assert (
        census._snapshot_contract_error(records[0], target_date="2026-07-30")
        == "source_payload_hash_mismatch"
    )


def test_capture_normalizes_nonfinite_numbers_before_source_hashing():
    records = census.capture_market_snapshots(
        "secret-token",
        target_date="2026-07-30",
        captured_at=datetime.fromisoformat("2026-07-30T10:00:00+09:00"),
        venues=("KRX",),
        panels=("liquid_common",),
        fetcher=lambda *_args, **_kwargs: [
            {
                "Code": "005930",
                "Name": "삼성전자",
                "Price": "NaN",
                "ChangeRate": "Infinity",
                "Volume": "-Infinity",
            }
        ],
    )

    row = records[0]["rows"][0]
    assert row["current_price"] is None
    assert row["change_rate_pct"] is None
    assert row["volume"] is None
    assert census._snapshot_contract_error(records[0], target_date="2026-07-30") == ""


def test_opportunity_episode_id_is_stable_and_resets_after_declared_gap():
    base = {
        "schema_version": census.SCHEMA_VERSION,
        "target_date": "2026-07-30",
        "venue": "KRX",
        "session": "KRX_REGULAR",
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
    snapshots = [
        {**base, "captured_at": "2026-07-30T10:00:00+09:00"},
        {**base, "captured_at": "2026-07-30T10:05:00+09:00"},
        {**base, "captured_at": "2026-07-30T10:20:01+09:00"},
    ]

    episodes = census._build_episodes(
        snapshots,
        panel="liquid_common",
        top_n=20,
    )

    assert len(episodes) == 2
    assert episodes[0]["snapshot_count"] == 2
    assert episodes[0]["opportunity_episode_id"].startswith("MOC-EPI-")
    assert (
        episodes[0]["opportunity_episode_id"] != episodes[1]["opportunity_episode_id"]
    )


def test_named_primary_metric_exists_and_missing_contracts_fail_closed(tmp_path):
    snapshot_path = tmp_path / "snapshots.jsonl"
    pipeline_path = tmp_path / "pipeline.jsonl"
    ai_path = tmp_path / "ai.jsonl"
    _write_jsonl(
        snapshot_path,
        [
            {
                "schema_version": census.SCHEMA_VERSION,
                "target_date": "2026-07-30",
                "captured_at": "2026-07-30T10:00:00+09:00",
                "venue": "KRX",
                "session": "KRX_REGULAR",
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
        ],
    )
    _write_jsonl(pipeline_path, [])
    _write_jsonl(ai_path, [])

    report = census.build_report(
        "2026-07-30",
        snapshot_path=snapshot_path,
        pipeline_path=pipeline_path,
        ai_trace_path=ai_path,
        symbol_master_path=tmp_path / "missing-master.json",
        trigger_receipt_path=tmp_path / "missing-trigger.json",
    )
    summary = report["coverage"]["liquid_common"]["top_20"]["forward_exact"]

    assert (
        census.METRIC_CONTRACT["primary_decision_metric"]
        == "entry_ai_provider_reach_rate_pct"
    )
    assert summary["entry_ai_provider_reach_rate_pct"] == 0.0
    assert summary["denominator_unique_opportunity_episode_count"] == 1
    assert report["schema_version"] == census.REPORT_SCHEMA_VERSION
    assert report["primary_decision"]["metric"] == ("entry_ai_provider_reach_rate_pct")
    assert report["primary_decision"]["by_venue"]["KRX"] == {
        "denominator_unique_opportunity_episode_count": 0,
        "entry_ai_provider_reached_unique": 0,
        "entry_ai_provider_reach_rate_pct": 0.0,
        "promotion_recall_pct": 0.0,
        "terminal_coverage_reason_counts": {},
        "terminal_coverage_reason_count_sum": 0,
        "terminal_denominator_conservation_delta": 0,
        "terminal_denominator_conservation_status": "pass",
        "candidate_not_promoted_first_reason_counts": {},
        "candidate_not_promoted_first_reason_count_sum": 0,
        "candidate_not_promoted_first_reason_conservation_delta": 0,
        "candidate_not_promoted_first_reason_conservation_status": "pass",
        "ex_post_executable_opportunity": {
            "denominator_unique_opportunity_episode_count": 0,
            "exact_bbo_joined_count": 0,
            "exact_bbo_not_joined_count": 0,
            "exact_bbo_join_coverage_pct": 0.0,
            "executable_entry_eligible_count": 0,
            "primary_horizon_sec": 1200,
            "primary_label_counts": {},
            "primary_label_count_sum": 0,
            "resolved_outcome_count": 0,
            "right_censored_count": 0,
            "right_censored_pct": None,
            "pending_horizon_count": 0,
            "observed_cohort_source_quality_adjusted_ev_pct": None,
            "source_quality_adjusted_ev_pct": None,
            "economic_evidence_floor_met": False,
            "sample_floor": {
                "exact_bbo_join_coverage_pct_min": 95.0,
                "resolved_outcome_count_min": 20,
                "right_censored_pct_max": 20.0,
            },
            "full_external_population_ev_extrapolation_allowed": False,
            "path_order_basis": ("first_threshold_crossing_on_bounded_observations"),
            "continuous_first_hit_authority": False,
            "fill_feasibility_basis": "one_share_at_displayed_best_quantity",
            "actual_fill_claim": False,
            "spread_realization_basis": "entry_ask_to_exit_bid",
            "extra_slippage_model": ("zero_extra_for_one_share_displayed_best_level"),
            "ev_population_scope": (
                "bounded_exact_bbo_joined_external_opportunity_cohort_only"
            ),
            "by_session": {},
        },
    }
    assert report["status"] == "early_evidence_hold_sample"
    assert report["scanner_recall_state"] == "insufficient_evidence_scanner_recall"
    assert (
        "official_symbol_master_binding_missing" in report["instrumentation_blockers"]
    )
    assert "installed_trigger_contract_missing" in report["instrumentation_blockers"]
    assert report["source_quality"]["primary_symbol_master_lookup_counts"] == {
        "master_unavailable": 1
    }
    assert report["source_quality"]["primary_symbol_master_lookup_codes"] == {
        "master_unavailable": ["005930"]
    }
    assert report["source_quality"]["missing_session_capture_ids"] == []
    assert report["source_quality"]["missing_source_hash_snapshot_count"] == 1
    assert report["source_quality"]["verified_source_hash_snapshot_count"] == 0
    assert "capture_source_hash_missing" in report["instrumentation_blockers"]


def test_primary_master_eligible_terminal_reasons_conserve_denominator(
    tmp_path, monkeypatch
):
    snapshot_path = tmp_path / "snapshots.jsonl"
    pipeline_path = tmp_path / "pipeline.jsonl"
    ai_path = tmp_path / "ai.jsonl"
    _write_jsonl(
        snapshot_path,
        [
            {
                "schema_version": census.SCHEMA_VERSION,
                "target_date": "2026-07-30",
                "captured_at": "2026-07-30T10:00:00+09:00",
                "venue": "KRX",
                "session": "KRX_REGULAR",
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
        ],
    )
    _write_jsonl(
        pipeline_path,
        [
            {
                "stock_code": "005930",
                "stage": "scalping_scanner_candidate_pruned",
                "emitted_at": "2026-07-30T10:00:01+09:00",
                "fields": {"effective_venue": "KRX_REGULAR"},
            }
        ],
    )
    _write_jsonl(ai_path, [])

    class FakeMaster:
        def lookup(self, *_args, **_kwargs):
            return SimpleNamespace(
                status=SimpleNamespace(value="verified"),
                record=SimpleNamespace(
                    listing_market=SimpleNamespace(value="KOSPI"),
                    instrument_type=SimpleNamespace(value="EQUITY"),
                ),
            )

    monkeypatch.setattr(
        census,
        "_load_symbol_master_binding",
        lambda *_args, **_kwargs: (FakeMaster(), {"status": "verified"}),
    )
    report = census.build_report(
        "2026-07-30",
        snapshot_path=snapshot_path,
        pipeline_path=pipeline_path,
        ai_trace_path=ai_path,
        trigger_receipt_path=tmp_path / "missing-trigger.json",
    )

    primary = report["primary_decision"]["by_venue"]["KRX"]
    assert primary["denominator_unique_opportunity_episode_count"] == 1
    assert primary["terminal_coverage_reason_counts"] == {"candidate_not_promoted": 1}
    assert primary["terminal_coverage_reason_count_sum"] == 1
    assert primary["terminal_denominator_conservation_delta"] == 0
    assert primary["terminal_denominator_conservation_status"] == "pass"
    assert primary["candidate_not_promoted_first_reason_counts"] == {
        "reason_missing": 1
    }
    assert (
        report["source_quality"]["primary_candidate_not_promoted_reason_missing_count"]
        == 1
    )
    assert "scanner_prune_first_reason_missing" in report["instrumentation_blockers"]


def test_trigger_contract_requires_current_wrapper_and_installed_exact_lines(
    tmp_path, monkeypatch
):
    wrapper = tmp_path / "run_market_opportunity_census_intraday.sh"
    wrapper.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    wrapper.chmod(0o700)
    monkeypatch.setattr(census, "DEFAULT_TRIGGER_WRAPPER", wrapper)
    trigger_lines = [
        f"{prefix}{wrapper} # {marker}"
        for prefix, marker in zip(
            census.EXPECTED_TRIGGER_SCHEDULE_PREFIXES,
            census.EXPECTED_TRIGGER_MARKERS,
            strict=True,
        )
    ]
    canonical_lines = "\n".join(trigger_lines) + "\n"
    payload = {
        "schema_version": census.TRIGGER_SCHEMA_VERSION,
        "trigger_id": "MARKET_OPPORTUNITY_CENSUS_5MIN",
        "enabled": True,
        "contract_source": "installed_crontab_verified",
        "schedule_timezone": "Asia/Seoul",
        "capture_cadence_sec": census.CAPTURE_CADENCE_SEC,
        "installed_exec_start": str(wrapper),
        "wrapper_sha256": hashlib.sha256(wrapper.read_bytes()).hexdigest(),
        "trigger_lines": trigger_lines,
        "trigger_lines_sha256": hashlib.sha256(
            canonical_lines.encode("utf-8")
        ).hexdigest(),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    receipt = tmp_path / "installed_trigger.json"
    receipt.write_text(json.dumps(payload), encoding="utf-8")

    verified = census._load_trigger_contract(
        receipt,
        installed_crontab_text=canonical_lines,
        system_timezone="Asia/Seoul",
    )
    missing_line = census._load_trigger_contract(
        receipt,
        installed_crontab_text="\n".join(trigger_lines[:-1]) + "\n",
        system_timezone="Asia/Seoul",
    )
    payload["trigger_lines"][0] = payload["trigger_lines"][0].replace("*/5 8", "*/10 8")
    tampered_lines = "\n".join(payload["trigger_lines"]) + "\n"
    payload["trigger_lines_sha256"] = hashlib.sha256(
        tampered_lines.encode("utf-8")
    ).hexdigest()
    receipt.write_text(json.dumps(payload), encoding="utf-8")
    invalid_schedule = census._load_trigger_contract(
        receipt,
        installed_crontab_text=tampered_lines,
        system_timezone="Asia/Seoul",
    )

    assert verified["status"] == "verified"
    assert verified["reason_codes"] == []
    assert verified["trigger_lines_installed"] is True
    assert missing_line["status"] == "invalid"
    assert "trigger_lines_installed" in missing_line["reason_codes"]
    assert invalid_schedule["status"] == "invalid"
    assert "trigger_schedule" in invalid_schedule["reason_codes"]


def test_existing_pipeline_events_cover_source_watch_authority_and_submit_safety(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline.jsonl"
    ai_path = tmp_path / "ai.jsonl"
    common = {
        "stock_code": "005930",
        "emitted_at": "2026-07-30T10:00:01+09:00",
    }
    _write_jsonl(
        pipeline_path,
        [
            {
                **common,
                "stage": "scalping_scanner_candidate_pruned",
                "fields": {"effective_venue": "KRX_REGULAR"},
            },
            {
                **common,
                "stage": "scalping_scanner_candidate_promoted",
                "fields": {
                    "effective_venue": "KRX_REGULAR",
                    "scanner_promotion_id": "SCANPROM-1",
                },
            },
            {
                **common,
                "record_id": 42,
                "stage": "scalping_scanner_runtime_target_attach",
                "fields": {
                    "effective_venue": "KRX_REGULAR",
                    "scanner_promotion_id": "SCANPROM-1",
                    "runtime_target_attach_outcome": "attached",
                },
            },
            {
                **common,
                "record_id": 42,
                "stage": "scalp_entry_action_decision_snapshot",
                "fields": {
                    "effective_venue": "KRX_REGULAR",
                    "scanner_promotion_id": "SCANPROM-1",
                    "decision_authority": "existing_entry_owner",
                },
            },
            {
                **common,
                "record_id": 42,
                "stage": "entry_submit_revalidation_block",
                "fields": {
                    "effective_venue": "KRX_REGULAR",
                    "scanner_promotion_id": "SCANPROM-1",
                    "block_reason": "stale_context_or_quote",
                },
            },
        ],
    )
    _write_jsonl(ai_path, [])

    index = census._load_stage_index(
        pipeline_path,
        ai_path,
        target_date="2026-07-30",
    )

    assert len(index["005930"]["source_seen"]) == 2
    assert len(index["005930"]["candidate_evaluated"]) == 2
    assert len(index["005930"]["watch_admitted"]) == 1
    assert len(index["005930"]["runtime_watch_attached"]) == 1
    assert len(index["005930"]["entry_authority_decided"]) == 1
    assert len(index["005930"]["submit_safety_checked"]) == 1
    assert index["005930"]["submit_safety_checked"][0]["raw_stage"] == (
        "entry_submit_revalidation_block"
    )


def test_exact_terminal_reason_preserves_submit_safety_block(tmp_path):
    pipeline_path = tmp_path / "pipeline.jsonl"
    ai_path = tmp_path / "ai.jsonl"
    promotion_id = "SCANPROM-BLOCKED"
    _write_jsonl(
        pipeline_path,
        [
            {
                "stock_code": "005930",
                "record_id": 42,
                "stage": stage,
                "emitted_at": f"2026-07-30T10:00:0{index}+09:00",
                "fields": {
                    "effective_venue": "KRX_REGULAR",
                    "scanner_promotion_id": promotion_id,
                    **(
                        {"runtime_target_attach_outcome": "attached"}
                        if stage == "scalping_scanner_runtime_target_attach"
                        else {}
                    ),
                    **(
                        {"block_reason": "stale_context_or_quote"}
                        if stage == "entry_submit_revalidation_block"
                        else {}
                    ),
                },
            }
            for index, stage in enumerate(
                [
                    "scalping_scanner_candidate_promoted",
                    "scalping_scanner_runtime_target_attach",
                    "scalping_scanner_fast_precheck",
                    "scalping_scanner_heavy_eval_completion",
                    "scalp_entry_action_decision_snapshot",
                    "entry_submit_revalidation_block",
                ]
            )
        ],
    )
    _write_jsonl(
        ai_path,
        [
            {
                "stock_code": "005930",
                "record_id": 42,
                "endpoint": "scalping_entry",
                "decision_ts": "2026-07-30T10:00:04+09:00",
                "effective_venue": "KRX_REGULAR",
                "provider_called": True,
                "provider_actual": "openai",
                "action": "BUY",
            }
        ],
    )
    stage_index = census._load_stage_index(
        pipeline_path,
        ai_path,
        target_date="2026-07-30",
    )

    row = census._coverage_row(
        {
            "venue": "KRX",
            "session": "KRX_REGULAR",
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "first_census_at": datetime.fromisoformat("2026-07-30T10:00:00+09:00"),
        },
        stage_index,
        after=datetime.fromisoformat("2026-07-30T10:00:00+09:00"),
        before=datetime.fromisoformat("2026-07-30T10:05:00+09:00"),
        require_venue=True,
        require_lineage=True,
    )

    assert row["terminal_coverage_reason"] == "submit_safety_block"
    assert row["stage_reason_codes"]["submit_safety_checked"] == [
        "stale_context_or_quote"
    ]


def test_candidate_prune_reason_is_preserved_for_scanner_attribution(tmp_path):
    pipeline_path = tmp_path / "pipeline.jsonl"
    ai_path = tmp_path / "ai.jsonl"
    _write_jsonl(
        pipeline_path,
        [
            {
                "stock_code": "005930",
                "stage": "scalping_scanner_candidate_pruned",
                "emitted_at": "2026-07-30T10:00:01+09:00",
                "fields": {
                    "effective_venue": "KRX_REGULAR",
                    "reason": "generic_noncanonical_reason",
                    "scanner_prune_reason": "general_slot_limit",
                    "scanner_block_reason": "less_specific_fallback",
                },
            },
            {
                "stock_code": "005930",
                "stage": "scalping_scanner_candidate_pruned",
                "emitted_at": "2026-07-30T10:00:02+09:00",
                "fields": {
                    "effective_venue": "KRX_REGULAR",
                    "scanner_prune_reason": "market_gainer_reserved_full",
                },
            },
        ],
    )
    _write_jsonl(ai_path, [])

    stage_index = census._load_stage_index(
        pipeline_path,
        ai_path,
        target_date="2026-07-30",
    )
    row = census._coverage_row(
        {
            "venue": "KRX",
            "session": "KRX_REGULAR",
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "first_census_at": datetime.fromisoformat("2026-07-30T10:00:00+09:00"),
        },
        stage_index,
        after=datetime.fromisoformat("2026-07-30T10:00:00+09:00"),
        before=datetime.fromisoformat("2026-07-30T10:05:00+09:00"),
        require_venue=True,
        require_lineage=True,
    )

    assert row["terminal_coverage_reason"] == "candidate_not_promoted"
    assert row["stage_reason_codes"]["candidate_evaluated"] == [
        "general_slot_limit",
        "market_gainer_reserved_full",
    ]
    assert row["first_stage_reason_code"]["candidate_evaluated"] == (
        "general_slot_limit"
    )

    summary = census._summarize_rows_base([row])
    assert summary["candidate_not_promoted_first_reason_counts"] == {
        "general_slot_limit": 1
    }
    assert summary["candidate_not_promoted_first_reason_count_sum"] == 1
    assert summary["candidate_not_promoted_first_reason_conservation_delta"] == 0
    assert summary["candidate_not_promoted_first_reason_conservation_status"] == "pass"

    missing_reason_row = {
        **row,
        "first_stage_reason_code": {
            **row["first_stage_reason_code"],
            "candidate_evaluated": None,
        },
    }
    missing_reason_summary = census._summarize_rows_base([missing_reason_row])
    assert missing_reason_summary["candidate_not_promoted_first_reason_counts"] == {
        "reason_missing": 1
    }


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
    assert forward["stage_counts"]["fast_precheck"] == 0
    assert forward["stage_counts"]["entry_ai_trace"] == 0
    assert forward["stage_counts"]["entry_ai_provider_called"] == 0
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


def test_report_forward_exact_joins_pipeline_and_ai_by_scanner_lineage(tmp_path):
    snapshot_path = tmp_path / "snapshots.jsonl"
    pipeline_path = tmp_path / "pipeline.jsonl"
    ai_path = tmp_path / "ai.jsonl"
    _write_jsonl(
        snapshot_path,
        [
            {
                "schema_version": census.SCHEMA_VERSION,
                "target_date": "2026-07-30",
                "captured_at": "2026-07-30T10:00:00+09:00",
                "venue": "KRX",
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
        ],
    )
    _write_jsonl(
        pipeline_path,
        [
            {
                "stage": "scalping_scanner_candidate_promoted",
                "stock_code": "005930",
                "emitted_at": "2026-07-30T10:00:01+09:00",
                "fields": {
                    "effective_venue": "KRX_REGULAR",
                    "scanner_promotion_id": "SCANPROM-005930-1",
                    "source_signature": "PREV_CLOSE_GAINER,PRICE_JUMP_START",
                },
            },
            {
                "stage": "scalping_scanner_fast_precheck",
                "record_id": 42,
                "stock_code": "005930",
                "emitted_at": "2026-07-30T10:00:02+09:00",
                "fields": {
                    "effective_venue": "KRX_REGULAR",
                    "scanner_promotion_id": "SCANPROM-005930-1",
                },
            },
            {
                "stage": "scalping_scanner_heavy_eval_completion",
                "record_id": 42,
                "stock_code": "005930",
                "emitted_at": "2026-07-30T10:00:03+09:00",
                "fields": {
                    "effective_venue": "KRX_REGULAR",
                    "scanner_promotion_id": "SCANPROM-005930-1",
                },
            },
        ],
    )
    _write_jsonl(
        ai_path,
        [
            {
                "endpoint": "analyze_target",
                "record_id": "42",
                "request_id": "analyze_target:005930:1",
                "stock_code": "005930",
                "decision_ts": "2026-07-30T10:00:05+09:00",
                "effective_venue": "KRX_REGULAR",
                "action": "WAIT",
                "provider_called": True,
                "provider_actual": "openai",
            }
        ],
    )

    report = census.build_report(
        "2026-07-30",
        snapshot_path=snapshot_path,
        pipeline_path=pipeline_path,
        ai_trace_path=ai_path,
    )
    summary = report["coverage"]["liquid_common"]["top_10"]["forward_exact"]
    detail = report["opportunity_details"]["liquid_common"]["top_10"]["forward_exact"][
        0
    ]

    assert summary["stage_counts"]["scanner_promoted"] == 1
    assert summary["stage_counts"]["heavy_eval"] == 1
    assert summary["stage_counts"]["entry_ai_provider_called"] == 1
    assert summary["prev_close_gainer_source_promotion_count"] == 1
    assert (
        summary["stage_latency_from_scanner_promoted_sec"]["entry_ai_provider_called"][
            "p50_sec"
        ]
        == 4.0
    )
    assert detail["scanner_lineage"]["record_ids"] == ["42"]
    assert detail["entry_ai_actions"] == ["WAIT"]


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


def test_coverage_records_scanner_to_ai_latency_and_terminal_owner():
    promoted_at = datetime.fromisoformat("2026-07-30T10:00:00+09:00")
    row = census._coverage_row(
        {
            "venue": "NXT",
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "first_census_at": promoted_at,
        },
        {
            "005930": {
                "scanner_promoted": [
                    {
                        "ts": promoted_at,
                        "venue": "NXT",
                        "reason": "promoted",
                        "scanner_promotion_id": "SCANPROM-005930-1",
                        "source_signature": "PREV_CLOSE_GAINER",
                    }
                ],
                "fast_precheck": [
                    {
                        "ts": datetime.fromisoformat("2026-07-30T10:00:01+09:00"),
                        "venue": "NXT",
                        "record_id": "42",
                        "scanner_promotion_id": "SCANPROM-005930-1",
                    }
                ],
                "entry_ai_provider_called": [
                    {
                        "ts": datetime.fromisoformat(
                            "2026-07-30T10:00:03.500000+09:00"
                        ),
                        "venue": "NXT",
                        "record_id": "42",
                        "provider_called": True,
                    }
                ],
            }
        },
        after=promoted_at,
        require_venue=True,
        require_lineage=True,
    )

    assert row["terminal_coverage_reason"] == "entry_authority_decision_gap"
    assert row["stage_latency_from_scanner_promoted_sec"]["fast_precheck"] == 1.0
    assert (
        row["stage_latency_from_scanner_promoted_sec"]["entry_ai_provider_called"]
        == 3.5
    )
    summary = census._summarize_rows_base([row])
    assert summary["terminal_coverage_reason_counts"] == {
        "entry_authority_decision_gap": 1
    }
    assert summary["scanner_lineage_status_counts"] == {
        "scanner_promotion_lineage_proven": 1
    }
    assert summary["prev_close_gainer_source_promotion_count"] == 1
    assert summary["stage_latency_from_scanner_promoted_sec"][
        "entry_ai_provider_called"
    ] == {
        "sample_count": 1,
        "p50_sec": 3.5,
        "p95_sec": 3.5,
        "max_sec": 3.5,
    }
    assert row["scanner_lineage"] == {
        "required": True,
        "status": "scanner_promotion_lineage_proven",
        "scanner_promotion_id": "SCANPROM-005930-1",
        "record_ids": ["42"],
        "source_signature": "PREV_CLOSE_GAINER",
        "prev_close_gainer_source": True,
    }


def test_primary_provider_rate_excludes_provider_reach_after_detection_sla():
    census_at = datetime.fromisoformat("2026-07-30T10:00:00+09:00")
    promoted_at = datetime.fromisoformat("2026-07-30T10:02:01+09:00")
    row = census._coverage_row(
        {
            "venue": "KRX",
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "first_census_at": census_at,
        },
        {
            "005930": {
                "scanner_promoted": [
                    {
                        "ts": promoted_at,
                        "venue": "KRX",
                        "scanner_promotion_id": "SCANPROM-005930-LATE",
                    }
                ],
                "fast_precheck": [
                    {
                        "ts": promoted_at,
                        "venue": "KRX",
                        "record_id": "late-42",
                        "scanner_promotion_id": "SCANPROM-005930-LATE",
                    }
                ],
                "entry_ai_provider_called": [
                    {
                        "ts": datetime.fromisoformat("2026-07-30T10:02:02+09:00"),
                        "venue": "KRX",
                        "record_id": "late-42",
                        "provider_called": True,
                    }
                ],
            }
        },
        after=census_at,
        before=datetime.fromisoformat("2026-07-30T10:05:00+09:00"),
        require_venue=True,
        require_lineage=True,
    )

    summary = census._summarize_rows_base([row])

    assert row["scanner_detection_latency_sec"] == 121.0
    assert row["scanner_detection_sla_met"] is False
    assert summary["stage_counts"]["entry_ai_provider_called"] == 1
    assert summary["entry_ai_provider_reached_within_sla_count"] == 0
    assert summary["entry_ai_provider_reach_rate_pct"] == 0.0


def test_forward_lineage_does_not_join_next_promotion_ai_result():
    first_promotion_at = datetime.fromisoformat("2026-07-30T10:00:00+09:00")
    second_promotion_at = datetime.fromisoformat("2026-07-30T10:05:00+09:00")
    row = census._coverage_row(
        {
            "venue": "KRX",
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "first_census_at": first_promotion_at,
        },
        {
            "005930": {
                "scanner_promoted": [
                    {
                        "ts": first_promotion_at,
                        "venue": "KRX",
                        "scanner_promotion_id": "SCANPROM-005930-1",
                    },
                    {
                        "ts": second_promotion_at,
                        "venue": "KRX",
                        "scanner_promotion_id": "SCANPROM-005930-2",
                    },
                ],
                "fast_precheck": [
                    {
                        "ts": datetime.fromisoformat("2026-07-30T10:00:01+09:00"),
                        "venue": "KRX",
                        "record_id": "42",
                        "scanner_promotion_id": "SCANPROM-005930-1",
                    }
                ],
                "entry_ai_provider_called": [
                    {
                        "ts": datetime.fromisoformat("2026-07-30T10:05:03+09:00"),
                        "venue": "KRX",
                        "record_id": "42",
                        "provider_called": True,
                    }
                ],
            }
        },
        after=first_promotion_at,
        require_venue=True,
        require_lineage=True,
    )

    assert row["stage_reached"]["scanner_promoted"] is True
    assert row["stage_reached"]["fast_precheck"] is True
    assert row["stage_reached"]["entry_ai_provider_called"] is False
    assert row["terminal_coverage_reason"] == "scanner_heavy_eval_gap"


def test_forward_exact_does_not_join_event_after_session_boundary():
    census_at = datetime.fromisoformat("2026-07-30T15:29:30+09:00")
    row = census._coverage_row(
        {
            "venue": "KRX",
            "session": "KRX_REGULAR",
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "first_census_at": census_at,
        },
        {
            "005930": {
                "scanner_promoted": [
                    {
                        "ts": datetime.fromisoformat("2026-07-30T15:30:01+09:00"),
                        "venue": "KRX",
                        "session": "OUTSIDE_KRX_BUY_WINDOW",
                        "scanner_promotion_id": "SCANPROM-005930-AFTER-CLOSE",
                    }
                ]
            }
        },
        after=census_at,
        before=datetime.fromisoformat("2026-07-30T15:34:30+09:00"),
        require_venue=True,
        require_lineage=True,
    )

    assert row["stage_reached"]["scanner_promoted"] is False
    assert row["scanner_lineage"]["status"] == ("not_applicable_no_scanner_promotion")
    assert row["terminal_coverage_reason"] == ("scanner_discovery_gap_or_unobserved")


def test_current_heavy_eval_completion_stage_is_counted():
    assert (
        "scalping_scanner_heavy_eval_completion"
        in census.PIPELINE_STAGE_MAP["heavy_eval"]
    )
    assert "scanner_async_eval_dispatched" in census.PIPELINE_STAGE_MAP["heavy_eval"]


def test_ex_post_opportunity_uses_exact_route_bbo_and_effective_cost(tmp_path):
    start = datetime.fromisoformat("2026-09-02T10:00:00+09:00")
    pipeline_path = tmp_path / "pipeline.jsonl"
    ai_path = tmp_path / "ai.jsonl"
    _write_jsonl(
        pipeline_path,
        [
            _prune_bbo_event(start + timedelta(seconds=1), bid=999, ask=1000),
            _prune_bbo_event(start + timedelta(seconds=30), bid=1006, ask=1007),
        ],
    )
    _write_jsonl(ai_path, [])
    bbo_index: dict = {}
    gap_counts = Counter()

    stage_index = census._load_stage_index(
        pipeline_path,
        ai_path,
        target_date="2026-09-02",
        executable_bbo_index=bbo_index,
        executable_bbo_gap_counts=gap_counts,
    )
    row = census._coverage_row(
        {
            "venue": "KRX",
            "session": "KRX_REGULAR",
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "first_census_at": start,
        },
        stage_index,
        after=start,
        before=start + timedelta(seconds=census.OPPORTUNITY_VALIDITY_SEC),
        require_venue=True,
        require_lineage=True,
        executable_bbo_index=bbo_index,
        observation_watermark=start + timedelta(minutes=21),
        round_trip_cost_pct=0.23,
    )

    outcome = row["ex_post_executable_opportunity"]
    assert gap_counts == {}
    assert outcome["status"] == "source_quality_valid"
    assert outcome["entry_best_ask"] == 1000
    assert outcome["entry_best_ask_qty"] == 100
    assert outcome["primary_outcome"]["label"] == "target_first"
    assert outcome["primary_outcome"]["gross_return_pct"] == 0.6
    assert outcome["primary_outcome"]["cost_adjusted_return_pct"] == 0.37


def test_ex_post_timeout_lag_respects_each_bbo_source_cadence():
    start = datetime.fromisoformat("2026-09-02T10:00:00+09:00")
    entry = {
        "observed_at": start,
        "observed_epoch": start.timestamp(),
        "best_ask": 1000,
    }
    delayed_timeout = {
        "observed_at": start + timedelta(seconds=1220),
        "observed_epoch": (start + timedelta(seconds=1220)).timestamp(),
        "best_bid": 1000,
        "best_bid_qty": 10,
        "timeout_max_lag_sec": census.CAPTURE_CADENCE_TOLERANCE_SEC,
    }

    direct = census._ex_post_horizon_outcome(
        [delayed_timeout],
        entry=entry,
        horizon_sec=1200,
        round_trip_cost_pct=0.23,
        observation_watermark=start + timedelta(seconds=1300),
    )
    promoted = census._ex_post_horizon_outcome(
        [
            {
                **delayed_timeout,
                "timeout_max_lag_sec": census.EX_POST_TIMEOUT_MAX_LAG_SEC,
            }
        ],
        entry=entry,
        horizon_sec=1200,
        round_trip_cost_pct=0.23,
        observation_watermark=start + timedelta(seconds=1300),
    )

    assert direct["label"] == "timeout_exit"
    assert direct["elapsed_sec"] == 1220.0
    assert promoted["label"] == "right_censored_no_timeout_bbo"
    assert promoted["cost_adjusted_return_pct"] is None


def test_ex_post_index_includes_promoted_ws_bundle_and_deduplicates(tmp_path):
    start = datetime.fromisoformat("2026-09-02T10:00:00+09:00")
    pipeline_path = tmp_path / "pipeline.jsonl"
    ai_path = tmp_path / "ai.jsonl"
    event = _promoted_ws_bundle_event(start)
    repeated = json.loads(json.dumps(event))
    repeated["emitted_at"] = (start + timedelta(seconds=2)).isoformat()
    _write_jsonl(pipeline_path, [event, repeated])
    _write_jsonl(ai_path, [])
    bbo_index: dict = {}
    gap_counts = Counter()

    census._load_stage_index(
        pipeline_path,
        ai_path,
        target_date="2026-09-02",
        executable_bbo_index=bbo_index,
        executable_bbo_gap_counts=gap_counts,
    )

    observations = bbo_index["005930"]["KRX"]["KRX_REGULAR"]
    assert gap_counts == {}
    assert len(observations) == 1
    assert observations[0]["price_source"] == ("existing_ws_route_scoped_0d_snapshot")
    assert observations[0]["best_bid_qty"] == 100
    assert observations[0]["best_ask_qty"] == 100


def test_external_snapshot_bbo_validates_exact_scope():
    captured_at = datetime.fromisoformat("2026-09-02T10:00:00+09:00")
    snapshot = {
        "capture_id": "MOC-1",
        "target_date": "2026-09-02",
        "venue": "KRX",
        "session": "KRX_REGULAR",
    }
    row = {
        "stock_code": "005930",
        "executable_bbo_observation": {
            "schema_version": census.EXTERNAL_BBO_OBSERVATION_SCHEMA_VERSION,
            "status": "captured",
            "gap_reason": "not_applicable_capture_pass",
            "request_attempted": True,
            "request_code": "005930",
            "response_request_code": "005930",
            "stock_code": "005930",
            "expected_observed_venue": "KRX",
            "request_started_epoch": captured_at.timestamp(),
            "request_completed_epoch": captured_at.timestamp() + 0.2,
            "observed_epoch": captured_at.timestamp() + 0.1,
            "quote_age_ms": 100.0,
            "best_bid": 999,
            "best_ask": 1000,
            "best_bid_qty": 12,
            "best_ask_qty": 10,
            "price_source": ("ka10004_external_market_census_exact_request_code"),
            "source_quality_pass": True,
            "daily_budget_reservation": {
                "status": "reserved",
                "reserved": True,
                "attempt_ordinal": 1,
                "daily_request_cap": census.EXTERNAL_BBO_MAX_REQUESTS_PER_KST_DATE,
            },
            "decision_authority": ("external_market_census_bbo_observation_only"),
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "market_data_request_effect": True,
        },
    }

    observation, reason = census._external_snapshot_bbo_observation(
        snapshot,
        row,
        target_date="2026-09-02",
    )

    assert reason == "pass"
    assert observation is not None
    assert observation["venue"] == "KRX"
    assert observation["session"] == "KRX_REGULAR"
    assert observation["best_ask_qty"] == 10

    row["executable_bbo_observation"]["daily_budget_reservation"]["attempt_ordinal"] = (
        "malformed"
    )
    invalid_observation, invalid_reason = census._external_snapshot_bbo_observation(
        snapshot,
        row,
        target_date="2026-09-02",
    )
    assert invalid_observation is None
    assert invalid_reason == "external_census_daily_budget_reservation_invalid"


def test_promoted_ws_bundle_rejects_missing_source_only_authority():
    when = datetime.fromisoformat("2026-09-02T10:00:00+09:00")
    event = _promoted_ws_bundle_event(when)
    event["fields"].pop("runtime_effect")

    observations, gaps = census._promoted_ws_bbo_observations(
        event, target_date="2026-09-02"
    )

    assert observations == []
    assert gaps == ["promoted_ws_runtime_effect_missing"]


def test_prune_bbo_runtime_receipt_exposes_fresh_pid_contract(tmp_path):
    pipeline_path = tmp_path / "pipeline.jsonl"
    ai_path = tmp_path / "ai.jsonl"
    _write_jsonl(
        pipeline_path,
        [
            {
                "stage": "scalping_scanner_prune_bbo_source_loaded",
                "stock_code": "-",
                "emitted_at": "2026-09-02T09:01:00+09:00",
                "fields": {
                    "scanner_prune_observer_process_pid": 1234,
                    "scanner_prune_observer_configuration_status": (
                        "collector_created"
                    ),
                    "scanner_prune_observer_configuration_receipt_status": "emitted",
                    "observation_schema_version": (
                        census.PRUNE_BBO_OBSERVATION_SCHEMA_VERSION
                    ),
                    "decision_authority": "scanner_prune_bbo_observation_only",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "market_data_request_effect": True,
                },
            }
        ],
    )
    _write_jsonl(ai_path, [])
    receipts: list[dict] = []

    census._load_stage_index(
        pipeline_path,
        ai_path,
        target_date="2026-09-02",
        observer_runtime_receipts=receipts,
    )

    assert receipts == [
        {
            "emitted_at": datetime.fromisoformat("2026-09-02T09:01:00+09:00"),
            "process_pid": 1234,
            "configuration_status": "collector_created",
            "configuration_receipt_status": "emitted",
            "observation_schema_version": (census.PRUNE_BBO_OBSERVATION_SCHEMA_VERSION),
            "decision_authority": "scanner_prune_bbo_observation_only",
            "authority_contract_fields_present": True,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "market_data_request_effect": True,
        }
    ]


def test_ex_post_bbo_rejects_missing_fill_quantity():
    when = datetime.fromisoformat("2026-09-02T10:00:00+09:00")
    event = _prune_bbo_event(when, bid=999, ask=1000)
    event["fields"].pop("scanner_prune_observer_best_ask_qty")

    observation, reason = census._prune_bbo_observation(event, target_date="2026-09-02")

    assert observation is None
    assert reason == "required_numeric_field_missing"


def test_ex_post_bbo_rejects_conflicting_venue_provenance():
    when = datetime.fromisoformat("2026-09-02T10:00:00+09:00")
    event = _prune_bbo_event(when, bid=999, ask=1000)
    event["fields"]["venue"] = "NXT"

    observation, reason = census._prune_bbo_observation(event, target_date="2026-09-02")

    assert observation is None
    assert reason == "explicit_venue_conflict_or_invalid"


def test_ex_post_ev_remains_non_authoritative_until_full_floor():
    base_row = {
        "venue": "KRX",
        "stage_reached": {stage: False for stage in census.STAGE_ORDER},
        "stage_latency_from_scanner_promoted_sec": {},
        "terminal_coverage_reason": "scanner_discovery_gap_or_unobserved",
        "first_stage_reason_code": {},
        "scanner_lineage": {},
        "ex_post_executable_opportunity": {
            "exact_bbo_joined": True,
            "executable_entry_eligible": True,
            "primary_outcome": {
                "label": "target_first",
                "cost_adjusted_return_pct": 0.1,
            },
        },
    }

    thin = census._summarize_rows_base([base_row])["ex_post_executable_opportunity"]
    mature = census._summarize_rows_base([dict(base_row) for _ in range(20)])[
        "ex_post_executable_opportunity"
    ]

    assert thin["observed_cohort_source_quality_adjusted_ev_pct"] == 0.1
    assert thin["source_quality_adjusted_ev_pct"] is None
    assert thin["economic_evidence_floor_met"] is False
    assert mature["source_quality_adjusted_ev_pct"] == 0.1
    assert mature["economic_evidence_floor_met"] is True
    assert mature["full_external_population_ev_extrapolation_allowed"] is False

    split_rows = [
        {**base_row, "venue": "KRX", "session": "KRX_REGULAR"} for _ in range(10)
    ] + [
        {**base_row, "venue": "NXT", "session": "NXT_REGULAR_OVERLAP"}
        for _ in range(10)
    ]
    scope_summaries, all_scopes_met = census._summarize_ex_post_by_scope(split_rows)

    assert all_scopes_met is False
    assert scope_summaries["KRX|KRX_REGULAR"]["resolved_outcome_count"] == 10
    assert scope_summaries["NXT|NXT_REGULAR_OVERLAP"]["resolved_outcome_count"] == 10


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
            "primary_decision": {
                "panel": "liquid_common",
                "top_n": 20,
                "view": "forward_exact",
                "metric": "entry_ai_provider_reach_rate_pct",
                "by_venue": {
                    "KRX": {
                        "denominator_unique_opportunity_episode_count": 19,
                        "entry_ai_provider_reached_unique": 2,
                        "entry_ai_provider_reach_rate_pct": 10.53,
                        "promotion_recall_pct": 10.53,
                        "terminal_coverage_reason_counts": {
                            "scanner_discovery_gap_or_unobserved": 19,
                        },
                        "terminal_coverage_reason_count_sum": 19,
                        "terminal_denominator_conservation_delta": 0,
                        "terminal_denominator_conservation_status": "pass",
                        "candidate_not_promoted_first_reason_counts": {
                            "general_slot_limit": 19,
                        },
                        "candidate_not_promoted_first_reason_count_sum": 19,
                        "candidate_not_promoted_first_reason_conservation_delta": 0,
                        "candidate_not_promoted_first_reason_conservation_status": (
                            "pass"
                        ),
                    },
                },
            },
        }
    )
    assert "runtime_effect: `false`" in markdown
    assert "| KRX | 19 | 2 | 10.53 | 10.53 | 19 | 0 | pass |" in markdown
    assert "### Terminal Coverage Reasons" in markdown
    assert "KRX terminal coverage reasons:" in markdown
    assert "### Candidate Not Promoted First Reasons" in markdown
    assert "`general_slot_limit`=19" in markdown
    assert "conservation_status=`pass`" in markdown
    assert "external BBO request reservation conservation:" in markdown
    assert "status=`unknown`" in markdown
    assert "`standalone_buy`" in markdown


def test_markdown_is_stable_after_sorted_json_round_trip():
    empty_summary = census._summarize_rows([])
    report = {
        "target_date": "2026-07-30",
        "status": "ok",
        "coverage": {
            "liquid_common": {
                "top_20": {
                    "forward_exact": empty_summary,
                    "same_day_venue_consistent_retrospective": empty_summary,
                    "same_day_any_venue_retrospective_noncausal": empty_summary,
                }
            }
        },
        "primary_decision": {"by_venue": {}},
    }
    round_tripped = json.loads(json.dumps(report, sort_keys=True))

    assert census.render_markdown(report) == census.render_markdown(round_tripped)
