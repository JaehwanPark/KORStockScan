from datetime import datetime
import json

import pytest

from src.engine.monitoring.ws_receive_expectation import classify_receive_gap
from src.engine.monitoring.ws_receive_expectation import (
    DepthReceiveCadence,
    project_depth_cadence,
    classify_delay_quote_collection,
)
from src.engine.monitoring import intraday_ws_freshness_monitor as monitor


def delay_collection_row(age=0.8):
    source = DepthReceiveCadence(
        item="196170_NX",
        epoch=7,
        generation="7:196170_NX:1000",
        session="P",
        registered_at=1000,
    )
    for at in range(1001, 1514):
        wire = source.wire(float(at))
        source.normalized(float(at), wire)
    now = 1513 + age
    evidence = project_depth_cadence(
        source.freeze(active=True, required_types=["0B", "0D"], receiver_ready=True),
        now,
    )
    evidence["depth_source_sha256"] = "a" * 64
    return (
        dict(
            stock_code="196170",
            quote_route="NXT_ONLY",
            quote_transport_epoch="7",
            quote_route_sequence=513,
            route_depth_source_sha256="a" * 64,
            quote_observed_at_epoch=now,
            ws_last_0d_epoch=1513.0,
            quote_valid=age <= 0.7,
            quote_source_reason=(
                "valid" if age <= 0.7 else "depth_stale_or_clock_invalid"
            ),
            quote_collection_evidence=evidence,
        ),
        source,
    )


@pytest.mark.parametrize(
    "age,state",
    [
        (0.2, "locally_healthy"),
        (0.8, "expected_wait"),
        (1.5, "cadence_exceeded_unproven"),
    ],
)
def test_delay_collection_cadence_does_not_change_quote_eligibility(age, state):
    row, _ = delay_collection_row(age)
    before = dict(row)
    assert classify_delay_quote_collection(row, ledger_complete=True)["state"] == state
    assert row == before


@pytest.mark.parametrize(
    "change,state,reason",
    [
        (
            {"subscription_active": False},
            "collection_fault_confirmed",
            "required_depth_subscription_missing",
        ),
        (
            {"required_types": ["0B"]},
            "collection_fault_confirmed",
            "required_depth_subscription_missing",
        ),
        (
            {
                "missing_normalizations": 1,
                "wire_count": 514,
                "normalized_wire_id": 514,
                "last_loss_wire_id": 514,
                "last_loss_epoch": 1513.0,
            },
            "collection_fault_confirmed",
            "wire_to_normalized_loss",
        ),
        ({"transport_epoch": 8}, "contract_invalid", "collection_scope_mismatch"),
        ({"item": "196170_AL"}, "contract_invalid", "collection_scope_mismatch"),
        ({"receiver_ready": False}, "unobservable", "collection_boundary_unproven"),
        (
            {"normalized_route_sequence": 512},
            "unobservable",
            "snapshot_generation_unproven",
        ),
        ({"normalized_count": 512}, "contract_invalid", "collection_counter_conflict"),
        (
            {"last_loss_wire_id": -1},
            "contract_invalid",
            "normalization_loss_marker_invalid",
        ),
        ({"cadence_sample_count": 99}, "unobservable", "cadence_baseline_insufficient"),
        (
            {"depth_source_sha256": "b" * 64},
            "contract_invalid",
            "collection_generation_binding_invalid",
        ),
        ({"clock_invalid": True}, "contract_invalid", "collection_clock_invalid"),
    ],
)
def test_delay_collection_detects_new_loss_without_waiving_stale_guard(
    change, state, reason
):
    row, _ = delay_collection_row()
    row["quote_collection_evidence"].update(change)
    result = classify_delay_quote_collection(row, ledger_complete=True)
    assert (result["state"], result["reason"]) == (state, reason)
    assert row["quote_valid"] is False


def test_delay_collection_missing_ledger_and_legacy_receipt_are_unproven():
    row, _ = delay_collection_row()
    assert (
        classify_delay_quote_collection(row, ledger_complete=False)["state"]
        == "unobservable"
    )
    row.pop("quote_collection_evidence")
    assert (
        classify_delay_quote_collection(row, ledger_complete=True)["state"]
        == "unobservable"
    )


def test_old_collection_snapshot_never_proves_expected_wait():
    row, _ = delay_collection_row()
    row["quote_collection_evidence"]["as_of_epoch"] -= 0.1
    assert classify_delay_quote_collection(row, ledger_complete=True) == dict(
        state="unobservable", reason="collection_evidence_stale"
    )


def test_delay_cadence_cache_expires_and_never_imports_future_window():
    _, source = delay_collection_row()
    frozen = source.freeze(active=True, required_types=["0D"], receiver_ready=True)
    first = project_depth_cadence(frozen, 1513.8)
    saved = source._stats_cache["value"]
    assert project_depth_cadence(frozen, 1513.9)["cadence_sample_count"] == 512
    assert source._stats_cache["value"] is saved
    assert project_depth_cadence(frozen, 1602.1)["cadence_sample_count"] == 511
    # A future cache and an already full producer snapshot cannot backdate
    # the quantiles for an earlier source observation.
    past = project_depth_cadence(frozen, 1500.0)
    assert past["cadence_sample_count"] == 499 and first["cadence_sample_count"] == 512
    assert "_cadence_cache" not in past


def test_delay_cadence_pending_is_not_proven_loss_until_next_normalized_id():
    row, source = delay_collection_row()
    pending = source.wire(1514.0)
    view = source.freeze(active=True, required_types=["0D"], receiver_ready=True)
    assert view["missing_normalizations"] == 0
    wire = source.wire(1515.0)
    source.normalized(1515.0, wire)
    assert pending < wire
    assert source.missing_normalizations == 1
    assert len(source.gaps) <= 512 and len(source.delivery) <= 512
    assert project_depth_cadence(view, 1513.0)["cadence_sample_count"] == 512


def test_delay_cadence_isolates_loss_from_later_normalization_and_baseline():
    row, source = delay_collection_row(0.2)

    def observe(at):
        evidence = project_depth_cadence(
            source.freeze(active=True, required_types=["0D"], receiver_ready=True), at
        )
        evidence["depth_source_sha256"] = "a" * 64
        row.update(
            quote_observed_at_epoch=at,
            ws_last_0d_epoch=source.last_normalized,
            quote_route_sequence=source.normalized_route_sequence,
            quote_collection_evidence=evidence,
        )
        return classify_delay_quote_collection(row, ledger_complete=True)

    source.wire(1514.0)  # Admitted but never normalized.
    source.normalized(1515.0, source.wire(1515.0), source_sequence=514)
    lost = observe(1515.2)
    assert lost["state"] == "collection_fault_confirmed"
    assert len(source.gaps) == 512 and max(v for _, v in source.gaps) == 1
    assert observe(1515.3)["loss_event_id"] == lost["loss_event_id"]
    source.normalized(1516.0, source.wire(1516.0), source_sequence=515)
    assert observe(1516.2)["state"] == "locally_healthy"
    assert source.missing_normalizations == 1 and source.last_loss_wire_id == 515
    assert row["quote_valid"] is True
    source.wire(1517.0)
    source.normalized(1518.0, source.wire(1518.0), source_sequence=516)
    new_loss = observe(1518.2)
    assert new_loss["state"] == "collection_fault_confirmed"
    assert new_loss["loss_event_id"] != lost["loss_event_id"]
    assert source.missing_normalizations == 2


@pytest.mark.parametrize(
    "delta,invalid", [(0.0, False), (-0.0005, False), (-0.01, True)]
)
def test_delay_normalizer_millisecond_precision_is_not_clock_reversal(delta, invalid):
    source = DepthReceiveCadence(
        item="196170_NX", epoch=7, generation="7:x", session="P", registered_at=10.0
    )
    wire = source.wire(11.0)
    source.normalized(11.0 + delta, wire)
    assert source.clock_invalid is invalid


def test_original_delay_intent_retains_all_eight_native_quotes_and_unknown_wire_origin():
    from pathlib import Path
    import hashlib

    fixture = json.loads(
        (
            Path(__file__).parent / "fixtures/pre_submit_delay_cadence_20261027.json"
        ).read_text()
    )
    invalid = 0
    for receipt in fixture["native_quotes"]:
        raw = receipt["raw_line"].encode()
        assert hashlib.sha256(raw).hexdigest() == receipt["raw_sha256"]
        event = json.loads(raw)
        row = dict(event["fields"], stock_code=event["stock_code"])
        result = classify_delay_quote_collection(row, ledger_complete=True)
        assert result == dict(
            state="unobservable", reason="legacy_collection_evidence_missing"
        )
        invalid += str(row["quote_valid"]).lower() != "true"
    assert len(fixture["native_quotes"]) == 8 and invalid == 6


def stamp(clock):
    return datetime.fromisoformat(f"2026-09-10T{clock}+09:00")


def quiet_states():
    # Explicit native 0s receipts, not a clock-only opening-gap waiver.
    return {
        scope: {
            "market_session_state_contract_version": "kiwoom_0s_market_operation_v1",
            "market_session_state_market_scope": scope,
            "market_session_state_raw": raw,
            "market_session_state_normalized": "CALL_AUCTION",
            "market_session_state_known": True,
            "receive_timestamp": stamp("08:50:00").isoformat(),
            "exchange_time_raw": "085000",
            "market_session_remaining_raw": remaining,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
        for scope, raw, remaining in (("KRX", "2", "001000"), ("NXT", "T", "001030"))
    }


def write_session_events(path):
    path.write_text(
        json.dumps(
            {
                "target_date": "2026-09-10",
                "schema_version": 1,
                "decision_authority": "source_quality_only",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "session_events": list(quiet_states().values()),
            }
        )
    )
    return path


def stale_row(route="krx_regular"):
    return {
        "market_session_states_by_scope": quiet_states(),
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
        {"market_session_states_by_scope": {}},
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
        ("08:49:50", "krx_regular", "08:55:00", "verified_market_state_quiet_snapshot"),
        ("08:49:50", "nxt_only", "09:00:20", "verified_market_state_quiet_snapshot"),
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
        None,
        target_date="2026-09-10",
        as_of=stamp(at),
        market_session_receipts=monitor._load_market_session_state_receipts(
            "2026-09-10", write_session_events(tmp_path / "session.json")
        )[0],
    )
    assert provenance["selection_reason"] == reason
    assert provenance["current_freshness_usable"] is False
    assert bool(payload) is (reason == "verified_market_state_quiet_snapshot")


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
        market_session_events_path=write_session_events(tmp_path / "session.json"),
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
