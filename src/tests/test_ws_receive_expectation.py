from datetime import datetime
import json

import pytest

from src.engine.monitoring.ws_receive_expectation import classify_receive_gap
from src.engine.monitoring import intraday_ws_freshness_monitor as monitor


def stamp(clock):
    return datetime.fromisoformat(f"2026-09-10T{clock}+09:00")


def stale_row(route="krx_regular"):
    return {
        "stock_code": "005930",
        "subscribed": True,
        "registered_market_routes": [route],
        "freshness_state": "stale",
        "last_receive_age_sec": 120,
        "last_0b_age_sec": 120,
        "last_0d_age_sec": 120,
        "repair_recommended": True,
        "repair_reason": "subscription_stale",
        "recommended_repair": "remove_then_reg_backoff",
    }


@pytest.mark.parametrize("route", ["krx_regular", "nxt_only", "krx_nxt_integrated"])
@pytest.mark.parametrize(
    "clock,quiet",
    [
        ("08:49:59", False),
        ("08:50:00", True),
        ("08:59:59", True),
        ("09:00:30", False),
        ("09:05:00", False),
    ],
)
def test_opening_gap_boundaries_preserve_raw_ages(route, clock, quiet):
    raw = stale_row(route)
    raw["last_receive_age_sec"] = (stamp(clock) - stamp("08:49:50")).total_seconds()
    result = classify_receive_gap(raw, stamp(clock))
    assert result["expected_market_quiet"] is quiet
    assert result["repair_recommended"] is (not quiet)
    assert result["last_receive_age_sec"] == raw["last_receive_age_sec"]
    assert raw["freshness_state"] == "stale"
    assert result["freshness_state"] != "fresh"


@pytest.mark.parametrize(
    "routes,quiet",
    [
        (["nxt_only"], True),
        (["krx_regular"], False),
        (["krx_nxt_integrated"], False),
        (["nxt_only", "krx_regular"], False),
        (["unknown"], False),
        ([], False),
    ],
)
def test_nxt_resumes_at_090030_without_masking_open_krx(routes, quiet):
    row = {**stale_row(), "registered_market_routes": routes}
    assert (
        classify_receive_gap(row, stamp("09:00:00"))["expected_market_quiet"] is quiet
    )


@pytest.mark.parametrize(
    "extra",
    [
        {"subscribed": False},
        {"connected": False},
        {"login_ok": False},
        {"subscription_ack_ok": False},
        {"storage_healthy": False},
        {"connection_error": "closed"},
        {"storage_error": "disk_full"},
        {"repair_reason": "subscription_ack_timeout"},
        {"required_realtime_missing_types": ["00"]},
        {"required_realtime_missing_types": [{}]},
        {"registered_market_routes": ["unknown"]},
    ],
)
def test_explicit_failure_or_unknown_authority_is_never_muted(extra):
    result = classify_receive_gap({**stale_row(), **extra}, stamp("08:55:00"))
    assert result["expected_market_quiet"] is False
    assert result["repair_recommended"] is True


def test_naive_missing_time_and_weekend_do_not_create_a_waiver():
    for at in (
        None,
        datetime(2026, 9, 10, 8, 55),
        datetime.fromisoformat("2026-09-12T08:55:00+09:00"),
    ):
        assert classify_receive_gap(stale_row(), at)["expected_market_quiet"] is False


@pytest.mark.parametrize("age", [400, float("nan"), -1, "unknown"])
def test_preexisting_or_invalid_receive_gap_is_not_muted(age):
    row = {**stale_row(), "last_receive_age_sec": age}
    assert (
        classify_receive_gap(row, stamp("08:55:00"))["expected_market_quiet"] is False
    )


def test_fresh_quote_and_missing_trade_is_expected_but_not_executable_trade():
    row = {**stale_row(), "freshness_state": "fresh", "trade_tick_quiet": True}
    result = classify_receive_gap(row, stamp("08:55:00"))
    assert result["expected_market_quiet"] is True
    assert result["trade_tick_quiet"] is False
    assert result["observed_trade_tick_quiet"] is True
    live = classify_receive_gap({**row, "trade_tick_quiet": False}, stamp("08:55:00"))
    assert live["freshness_state"] == "fresh"


def test_persisted_quiet_snapshot_does_not_suppress_postopen_staleness():
    row = classify_receive_gap(stale_row(), stamp("08:59:50"))
    assert classify_receive_gap(row, stamp("08:59:51"))["expected_market_quiet"] is True
    assert classify_receive_gap(row, stamp("09:00:00"))["freshness_state"] == "stale"
    rows = monitor._snapshot_rows({"rows": [row]}, stale_ms=30000, elapsed_ms=15000)
    result = classify_receive_gap(rows[0], stamp("09:00:05"))
    assert result["expected_market_quiet"] is False
    assert result["freshness_state"] == "stale"
    assert result["repair_reason"] == "subscription_stale"
    assert result["repair_recommended"] is True


def test_persisted_quiet_metadata_cannot_overwrite_new_ack_failure():
    row = classify_receive_gap(stale_row(), stamp("08:55:00"))
    row.update(
        repair_reason="subscription_ack_timeout",
        repair_recommended=True,
        recommended_repair="inspect_ack",
    )
    result = classify_receive_gap(row, stamp("08:55:01"))
    assert result["expected_market_quiet"] is False
    assert result["repair_reason"] == "subscription_ack_timeout"
    assert result["repair_recommended"] is True
    assert result["recommended_repair"] == "inspect_ack"


def test_conflicting_fallback_routes_do_not_extend_krx_pause():
    row = stale_row()
    del row["registered_market_routes"]
    row.update(observed_market_route="nxt_only", venue="KRX")
    assert not classify_receive_gap(row, stamp("09:00:10"))["expected_market_quiet"]


@pytest.mark.parametrize(
    "fault",
    [
        {"connected": False},
        {"storage_error": "disk_full"},
        {"repair_reason": "subscription_ack_timeout"},
    ],
)
def test_dashboard_adapter_preserves_explicit_faults(fault):
    rows = monitor._snapshot_rows(
        {
            "stocks": {
                "005930": {
                    "last_realtime_type_ages_ms": {"0B": 120000, "0D": 120000},
                    "last_ws_market_route": "krx_regular",
                    **fault,
                }
            }
        },
        stale_ms=30000,
    )
    result = classify_receive_gap(rows[0], stamp("08:55:00"))
    assert not result["expected_market_quiet"]
    for key, value in fault.items():
        assert result[key] == value


def test_pipeline_persisted_no_tick_resumes_after_open():
    row = classify_receive_gap(
        {
            **stale_row(),
            "freshness_state": "no_tick",
            "last_receive_age_sec": None,
            "last_0b_age_sec": None,
            "last_0d_age_sec": None,
        },
        stamp("08:55:00"),
    )
    row["emitted_at"] = stamp("09:00:00").isoformat()
    result = monitor._pipeline_event_class(row, stale_ms=30000)
    assert not result["expected_market_quiet"]
    assert result["subscription_stale"]


@pytest.mark.parametrize("age", [float("nan"), -1, "invalid", True])
def test_invalid_snapshot_age_is_not_normalized_into_expected_absence(age):
    for snapshot in (
        {"rows": [{**stale_row(), "last_receive_age_sec": age}]},
        {
            "stocks": {
                "005930": {
                    "last_realtime_type_ages_ms": {"0B": age},
                    "last_ws_market_route": "krx_regular",
                }
            }
        },
    ):
        row = monitor._snapshot_rows(snapshot, stale_ms=30000)[0]
        assert not classify_receive_gap(row, stamp("08:55:00"))["expected_market_quiet"]


def test_historical_event_uses_its_own_time_and_keeps_decision_guard():
    row = {
        **stale_row(),
        "emitted_at": stamp("08:55:00").isoformat(),
        "stage": "fast_precheck",
        "scanner_ws_stale_backoff_reason": "persistent_ws_gap",
    }
    quiet = monitor._pipeline_event_class(row, stale_ms=30000)
    assert quiet["expected_market_quiet"] is True
    assert quiet["subscription_stale"] is False
    assert quiet["both_ws_stale"] is False
    assert quiet["decision_stage_stale_backoff"] is True
    row["emitted_at"] = stamp("09:05:00").isoformat()
    opened = monitor._pipeline_event_class(row, stale_ms=30000)
    assert opened["subscription_stale"] is True
    assert opened["both_ws_stale"] is True


def test_pipeline_age_only_gap_before_auction_remains_visible():
    row = {
        "venue": "KRX",
        "emitted_at": stamp("08:55:00").isoformat(),
        "ws_last_0b_age_ms": 600000,
        "ws_last_0d_age_ms": 600000,
    }
    result = monitor._pipeline_event_class(row, stale_ms=30000)
    assert result["expected_market_quiet"] is False
    assert result["both_ws_stale"] is True


@pytest.mark.parametrize(
    "file_time,route,at,reason",
    [
        ("08:49:50", "krx_regular", "08:55:00", "scheduled_opening_gap_snapshot"),
        ("08:49:50", "nxt_only", "09:00:20", "scheduled_opening_gap_snapshot"),
        ("08:49:50", "krx_regular", "09:00:20", "snapshot_stale"),
        ("08:49:50", "nxt_only", "09:00:30", "snapshot_stale"),
        ("08:40:00", "krx_regular", "08:55:00", "snapshot_stale"),
        ("08:49:50", "unknown", "08:55:00", "snapshot_stale"),
    ],
)
def test_event_driven_dashboard_pause_is_bounded_and_never_current_quote(
    tmp_path, monkeypatch, file_time, route, at, reason
):
    path = tmp_path / "snapshot.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "kiwoom_ws_dashboard_snapshot_v1",
                "generated_at": stamp(file_time).isoformat(),
                "stocks": {
                    "005930": {
                        "last_realtime_type_ages_ms": {"0B": 100, "0D": 100},
                        "last_ws_market_route": route,
                    }
                },
            }
        )
    )
    monkeypatch.setattr(monitor, "DEFAULT_DASHBOARD_SNAPSHOT_PATH", path)
    _, payload, provenance = monitor._resolve_snapshot(
        None, target_date="2026-09-10", as_of=stamp(at)
    )
    assert provenance["selection_reason"] == reason
    assert provenance["current_freshness_usable"] is False
    assert bool(payload) is (reason == "scheduled_opening_gap_snapshot")


def test_full_report_separates_quiet_from_fault_and_finalizes_by_event_time(tmp_path):
    pipeline = tmp_path / "pipeline.jsonl"
    threshold = tmp_path / "threshold.jsonl"
    snapshot = tmp_path / "snapshot.json"
    cache = tmp_path / "cache.json"
    event = {
        **stale_row(),
        "stage": "ws_snapshot",
        "emitted_at": stamp("08:55:00").isoformat(),
    }
    pipeline.write_text(json.dumps(event) + "\n")
    threshold.write_text("")
    snapshot.write_text(
        json.dumps(
            {"generated_at": stamp("08:55:00").isoformat(), "rows": [stale_row()]}
        )
    )
    kwargs = dict(
        pipeline_path=pipeline,
        threshold_path=threshold,
        subscription_snapshot_path=snapshot,
        incremental_state_path=cache,
    )
    report = monitor.build_report(
        "2026-09-10", generated_at=stamp("08:55:01").isoformat(), **kwargs
    )
    assert report["pipeline_counts"]["expected_market_quiet"] == 1
    assert report["pipeline_counts"].get("subscription_stale", 0) == 0
    assert report["snapshot_summary"]["expected_market_quiet_count"] == 1
    assert report["snapshot_summary"]["repair_recommended_count"] == 0
    assert report["snapshot_summary"]["receive_gap_evaluable_row_count"] == 0
    assert report["pipeline_rates"]["subscription_stale_rate_pct"] is None
    assert "order_ws_subscription_stale_repair_observability" not in {
        order["order_id"]
        for order in monitor._build_workorders(report, target_date="2026-09-10")
    }
    final = monitor.build_report(
        "2026-09-10",
        generated_at=stamp("20:10:00").isoformat(),
        finalize=True,
        **kwargs,
    )
    assert final["pipeline_counts"]["expected_market_quiet"] == 1
    assert final["snapshot_summary"]["expected_market_quiet_count"] == 1
    assert final["snapshot_summary"]["subscription_stale_like_count"] == 0

    pipeline.write_text(
        json.dumps(event)
        + "\n"
        + json.dumps({**event, "emitted_at": stamp("09:05:00").isoformat()})
        + "\n"
    )
    snapshot.write_text(
        json.dumps(
            {"generated_at": stamp("09:05:00").isoformat(), "rows": [stale_row()]}
        )
    )
    opened = monitor.build_report(
        "2026-09-10", generated_at=stamp("09:05:01").isoformat(), **kwargs
    )
    assert opened["pipeline_counts"]["subscription_stale"] == 1
    assert opened["pipeline_rates"]["subscription_stale_rate_pct"] == 100.0
    assert opened["snapshot_summary"]["repair_recommended_count"] == 1
