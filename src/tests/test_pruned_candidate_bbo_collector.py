from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.engine.monitoring import pruned_candidate_bbo_collector as collector_mod
from src.engine.monitoring.pruned_candidate_bbo_collector import (
    PrunedCandidateBBOCollector,
)

KST = timezone(timedelta(hours=9))


class _Clock:
    def __init__(self, value: float) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value


def _epoch(hour: int, minute: int, second: int = 0) -> float:
    return datetime(2026, 9, 2, hour, minute, second, tzinfo=KST).timestamp()


def _target(code: str = "005930") -> dict[str, str]:
    return {"Code": code, "Name": f"NAME-{code}"}


def _venue(venue: str = "KRX", session: str = "KRX_REGULAR") -> dict[str, str]:
    return {"effective_venue": venue, "market_session_bucket": session}


def test_global_collector_emits_secret_free_pid_configuration_receipt(
    monkeypatch,
) -> None:
    emitted: list[dict] = []
    monkeypatch.setattr(collector_mod, "_GLOBAL_COLLECTOR", None)
    monkeypatch.setattr(collector_mod.time, "time", lambda: _epoch(9, 5))
    monkeypatch.setattr(
        collector_mod,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, fields: emitted.append(
            {
                "pipeline": pipeline,
                "name": name,
                "code": code,
                "stage": stage,
                "fields": fields,
            }
        ),
    )

    collector = collector_mod.configure_global_collector("SECRET-TOKEN")

    assert collector is not None
    assert len(emitted) == 1
    receipt = emitted[0]
    assert receipt["stage"] == "scalping_scanner_prune_bbo_source_loaded"
    fields = receipt["fields"]
    assert fields["observation_schema_version"] == (
        collector_mod.OBSERVATION_SCHEMA_VERSION
    )
    assert fields["scanner_prune_observer_configuration_status"] == (
        "collector_created"
    )
    assert fields["scanner_prune_observer_configuration_receipt_status"] == ("emitted")
    assert fields["scanner_prune_observer_process_pid"] > 0
    assert fields["scanner_prune_observer_token_present"] is True
    assert fields["scanner_prune_observer_sample_offsets_sec"] == list(
        collector_mod.SAMPLE_OFFSETS_SEC
    )
    assert fields["scanner_prune_observer_episode_reset_gap_sec"] == 300.0
    assert fields["scanner_prune_observer_max_anchor_to_schedule_delay_sec"] == 2.0
    assert fields["scanner_prune_observer_market_data_request_effect"] is True
    assert "SECRET-TOKEN" not in str(receipt)
    assert fields["runtime_effect"] is False
    assert fields["allowed_runtime_apply"] is False
    assert fields["actual_order_submitted"] is False
    assert fields["broker_order_forbidden"] is True


def test_missing_global_collector_keeps_eligible_prune_visible(monkeypatch) -> None:
    monkeypatch.setattr(collector_mod, "_GLOBAL_COLLECTOR", None)

    result = collector_mod.offer_global_prune_observation(
        _target(),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-MISSING-HOOK",
        scan_rank=1,
        ranked_candidate_count=1,
        venue_fields=_venue(),
        observed_epoch=_epoch(9, 10),
    )

    assert result["eligible"] is True
    assert result["scanner_prune_observer_schedule_status"] == (
        "collector_not_configured"
    )
    assert result["scanner_prune_observer_configured"] is False
    assert result["runtime_effect"] is False
    assert result["actual_order_submitted"] is False


def test_collector_uses_exact_route_and_emits_source_only_bbo_receipt() -> None:
    clock = _Clock(_epoch(9, 10))
    fetch_calls: list[tuple[str, str, dict]] = []
    emitted: list[dict] = []

    def fetch(token, request_code, **kwargs):
        fetch_calls.append((token, request_code, kwargs))
        return {
            "source": "ka10004_rest_orderbook",
            "stock_code": "005930",
            "request_code": request_code,
            "rest_received_ts": clock.value,
            "best_bid": 70000,
            "best_ask": 70100,
            "best_bid_qty": 200,
            "best_ask_qty": 180,
            "bid_req_base_tm": "091000",
        }

    def emit(pipeline, name, code, stage, *, fields):
        emitted.append(
            {
                "pipeline": pipeline,
                "name": name,
                "code": code,
                "stage": stage,
                "fields": fields,
            }
        )

    collector = PrunedCandidateBBOCollector(
        "TOKEN",
        fetch_quote=fetch,
        emit_event=emit,
        clock=clock,
        autostart=False,
    )
    schedule = collector.offer(
        _target(),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-1",
        scan_rank=3,
        ranked_candidate_count=8,
        venue_fields=_venue(),
    )

    assert schedule["scanner_prune_observer_schedule_status"] == (
        "new_episode_scheduled"
    )
    assert schedule["scanner_prune_observer_request_code"] == "005930"
    assert schedule["scanner_prune_observer_anchor_to_schedule_delay_sec"] == 0.0
    assert collector.run_due_once(now_epoch=clock.value) is True
    assert fetch_calls == [
        (
            "TOKEN",
            "005930",
            {
                "explicit_request_code": True,
                "max_retries": 1,
                "request_owner": "scalping_scanner_prune_bbo_observation",
                "request_class": "source_only",
                "read_rate_max_wait_sec": 1.25,
                "return_meta": True,
            },
        )
    ]
    event = emitted[0]
    assert event["stage"] == "scalping_scanner_prune_bbo_observation"
    assert event["fields"]["scanner_prune_observer_status"] == "captured"
    assert event["fields"]["scanner_prune_observer_best_bid"] == 70000
    assert event["fields"]["scanner_prune_observer_best_ask"] == 70100
    assert event["fields"]["scanner_prune_observer_best_bid_qty"] == 200
    assert event["fields"]["scanner_prune_observer_best_ask_qty"] == 180
    assert event["fields"]["scanner_prune_observer_schedule_lag_sec"] == 0.0
    assert event["fields"]["decision_authority"] == (
        "scanner_prune_bbo_observation_only"
    )
    assert event["fields"]["runtime_effect"] is False
    assert event["fields"]["actual_order_submitted"] is False
    assert event["fields"]["broker_order_forbidden"] is True


def test_collector_reuses_stable_episode_and_clips_horizon_at_session_end() -> None:
    clock = _Clock(_epoch(15, 29, 59))
    collector = PrunedCandidateBBOCollector("TOKEN", clock=clock, autostart=False)

    first = collector.offer(
        _target(),
        reason="market_gainer_reserved_full",
        scan_generation_id="SCANGEN-1",
        scan_rank=1,
        ranked_candidate_count=4,
        venue_fields=_venue(),
    )
    second = collector.offer(
        _target(),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-2",
        scan_rank=2,
        ranked_candidate_count=4,
        venue_fields=_venue(),
        observed_epoch=clock.value + 0.5,
    )

    assert first["scanner_prune_observer_scheduled_offsets_sec"] == [0]
    assert second["scanner_prune_observer_schedule_status"] == (
        "existing_episode_reused"
    )
    assert (
        second["scanner_prune_observer_episode_id"]
        == (first["scanner_prune_observer_episode_id"])
    )


def test_collector_fails_closed_when_best_quantity_is_missing() -> None:
    clock = _Clock(_epoch(9, 10))
    emitted: list[dict] = []
    collector = PrunedCandidateBBOCollector(
        "TOKEN",
        fetch_quote=lambda _token, request_code, **_kwargs: {
            "source": "ka10004_rest_orderbook",
            "stock_code": request_code[:6],
            "request_code": request_code,
            "rest_received_ts": clock.value,
            "best_bid": 70000,
            "best_ask": 70100,
        },
        emit_event=lambda *_args, **kwargs: emitted.append(kwargs["fields"]),
        clock=clock,
        autostart=False,
    )
    collector.offer(
        _target(),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-QTY-GAP",
        scan_rank=1,
        ranked_candidate_count=1,
        venue_fields=_venue(),
    )

    assert collector.run_due_once(now_epoch=clock.value) is True
    assert emitted[0]["scanner_prune_observer_status"] == "source_quality_gap"
    assert emitted[0]["scanner_prune_observer_gap_reason"] == (
        "ka10004_best_quantity_missing_or_invalid"
    )
    assert emitted[0]["scanner_prune_observer_best_bid"] is None
    assert emitted[0]["scanner_prune_observer_best_ask"] is None


def test_collector_preserves_ka10004_rate_limit_as_first_gap_reason() -> None:
    clock = _Clock(_epoch(9, 10))
    emitted: list[dict] = []
    collector = PrunedCandidateBBOCollector(
        "TOKEN",
        fetch_quote=lambda *_args, **_kwargs: (
            {},
            {
                "request_owner": "scalping_scanner_prune_bbo_observation",
                "request_class": "source_only",
                "request_pid": 123,
                "request_attempt_count": 1,
                "read_rate_control_status": "admitted",
                "read_rate_control_reason": "shared_read_rate_admitted",
                "read_rate_control_waited_sec": 0.2,
                "rate_limit_detected": True,
            },
        ),
        emit_event=lambda *_args, **kwargs: emitted.append(kwargs["fields"]),
        clock=clock,
        autostart=False,
    )
    collector.offer(
        _target(),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-429",
        scan_rank=1,
        ranked_candidate_count=1,
        venue_fields=_venue(),
    )

    assert collector.run_due_once(now_epoch=clock.value) is True
    assert emitted[0]["scanner_prune_observer_gap_reason"] == "ka10004_rate_limited"
    assert emitted[0]["scanner_prune_observer_request_pid"] == 123
    assert emitted[0]["scanner_prune_observer_request_attempt_count"] == 1
    assert emitted[0]["scanner_prune_observer_rate_limit_detected"] is True


def test_collector_keeps_valid_snapshot_after_rate_limit_recovery() -> None:
    clock = _Clock(_epoch(9, 10))
    emitted: list[dict] = []
    collector = PrunedCandidateBBOCollector(
        "TOKEN",
        fetch_quote=lambda *_args, **_kwargs: (
            {
                "source": "ka10004_rest_orderbook",
                "stock_code": "005930",
                "request_code": "005930",
                "rest_received_ts": clock.value,
                "best_bid": 70000,
                "best_ask": 70100,
                "best_bid_qty": 200,
                "best_ask_qty": 180,
            },
            {
                "request_owner": "scalping_scanner_prune_bbo_observation",
                "request_class": "source_only",
                "request_attempt_count": 2,
                "read_rate_control_status": "admitted",
                "rate_limit_detected": True,
                "rate_limit_retry_exhausted": False,
            },
        ),
        emit_event=lambda *_args, **kwargs: emitted.append(kwargs["fields"]),
        clock=clock,
        autostart=False,
    )
    collector.offer(
        _target(),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-RECOVERED-429",
        scan_rank=1,
        ranked_candidate_count=1,
        venue_fields=_venue(),
    )

    assert collector.run_due_once(now_epoch=clock.value) is True
    assert emitted[0]["scanner_prune_observer_status"] == "captured"
    assert emitted[0]["scanner_prune_observer_gap_reason"] == (
        "not_applicable_capture_pass"
    )
    assert emitted[0]["scanner_prune_observer_rate_limit_detected"] is True
    assert emitted[0]["scanner_prune_observer_rate_limit_retry_exhausted"] is False


def test_collector_rotates_episode_only_after_observation_absence() -> None:
    clock = _Clock(_epoch(9, 10))
    collector = PrunedCandidateBBOCollector(
        "TOKEN",
        clock=clock,
        autostart=False,
        max_active_episodes=2,
        max_daily_requests=20,
    )
    first = collector.offer(
        _target(),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-1",
        scan_rank=1,
        ranked_candidate_count=1,
        venue_fields=_venue(),
    )
    rotated = collector.offer(
        _target(),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-2",
        scan_rank=1,
        ranked_candidate_count=1,
        venue_fields=_venue(),
        observed_epoch=clock.value + 301.0,
    )

    assert rotated["scanner_prune_observer_schedule_status"] == (
        "new_episode_scheduled"
    )
    assert (
        rotated["scanner_prune_observer_episode_id"]
        != (first["scanner_prune_observer_episode_id"])
    )


def test_deferred_episode_retries_with_same_id_when_capacity_frees() -> None:
    clock = _Clock(_epoch(15, 29, 59))
    collector = PrunedCandidateBBOCollector(
        "TOKEN",
        fetch_quote=lambda _token, request_code, **_kwargs: {
            "source": "ka10004_rest_orderbook",
            "stock_code": request_code[:6],
            "request_code": request_code,
            "rest_received_ts": clock.value,
            "best_bid": 100,
            "best_ask": 101,
        },
        emit_event=lambda *_args, **_kwargs: None,
        clock=clock,
        autostart=False,
        max_active_episodes=1,
        max_daily_requests=2,
    )
    collector.offer(
        _target("005930"),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-1",
        scan_rank=1,
        ranked_candidate_count=2,
        venue_fields=_venue(),
    )
    deferred = collector.offer(
        _target("000660"),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-1",
        scan_rank=2,
        ranked_candidate_count=2,
        venue_fields=_venue(),
    )
    assert deferred["scanner_prune_observer_schedule_status"] == (
        "active_episode_capacity_rejected"
    )
    assert collector.run_due_once(now_epoch=clock.value) is True
    clock.value += 0.5
    retried = collector.offer(
        _target("000660"),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-2",
        scan_rank=1,
        ranked_candidate_count=1,
        venue_fields=_venue(),
    )

    assert retried["scanner_prune_observer_schedule_status"] == (
        "new_episode_scheduled"
    )
    assert (
        retried["scanner_prune_observer_episode_id"]
        == (deferred["scanner_prune_observer_episode_id"])
    )
    assert retried["scanner_prune_observer_anchor_generation_id"] == "SCANGEN-1"
    assert (
        retried["scanner_prune_observer_anchor_epoch"]
        == deferred["scanner_prune_observer_anchor_epoch"]
    )
    assert retried["scanner_prune_observer_anchor_to_schedule_delay_sec"] == 0.5


def test_deferred_episode_does_not_spend_budget_after_anchor_latency_ceiling() -> None:
    clock = _Clock(_epoch(15, 29, 55))
    collector = PrunedCandidateBBOCollector(
        "TOKEN",
        fetch_quote=lambda _token, request_code, **_kwargs: {
            "source": "ka10004_rest_orderbook",
            "stock_code": request_code[:6],
            "request_code": request_code,
            "rest_received_ts": clock.value,
            "best_bid": 100,
            "best_ask": 101,
        },
        emit_event=lambda *_args, **_kwargs: None,
        clock=clock,
        autostart=False,
        max_active_episodes=1,
        max_daily_requests=20,
    )
    collector.offer(
        _target("005930"),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-1",
        scan_rank=1,
        ranked_candidate_count=2,
        venue_fields=_venue(),
    )
    deferred = collector.offer(
        _target("000660"),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-1",
        scan_rank=2,
        ranked_candidate_count=2,
        venue_fields=_venue(),
    )

    assert collector.run_due_once(now_epoch=clock.value) is True
    clock.value += 3.0
    assert collector.run_due_once(now_epoch=clock.value) is True
    retried = collector.offer(
        _target("000660"),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-2",
        scan_rank=1,
        ranked_candidate_count=1,
        venue_fields=_venue(),
    )

    assert deferred["scanner_prune_observer_schedule_status"] == (
        "active_episode_capacity_rejected"
    )
    assert retried["scanner_prune_observer_schedule_status"] == (
        "anchor_schedule_latency_exceeded"
    )
    assert (
        retried["scanner_prune_observer_episode_id"]
        == (deferred["scanner_prune_observer_episode_id"])
    )
    assert retried["scanner_prune_observer_scheduled_sample_count"] == 0
    assert retried["scanner_prune_observer_process_daily_scheduled_request_count"] == 2


def test_collector_preserves_explicit_nxt_route_and_fails_closed_on_capacity() -> None:
    clock = _Clock(_epoch(16, 0))
    collector = PrunedCandidateBBOCollector(
        "TOKEN",
        clock=clock,
        autostart=False,
        max_active_episodes=1,
    )
    first = collector.offer(
        _target("005930"),
        reason="reentry_cooldown_no_material_upgrade",
        scan_generation_id="SCANGEN-1",
        scan_rank=1,
        ranked_candidate_count=2,
        venue_fields=_venue("NXT", "NXT_REGULAR"),
    )
    rejected = collector.offer(
        _target("000660"),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-1",
        scan_rank=2,
        ranked_candidate_count=2,
        venue_fields=_venue("NXT", "NXT_REGULAR"),
    )
    rejected_again = collector.offer(
        _target("000660"),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-2",
        scan_rank=1,
        ranked_candidate_count=1,
        venue_fields=_venue("NXT", "NXT_REGULAR"),
        observed_epoch=clock.value + 1.0,
    )

    assert first["scanner_prune_observer_request_code"] == "005930_NX"
    assert first["scanner_prune_observer_expected_observed_venue"] == "NXT"
    assert rejected["scanner_prune_observer_schedule_status"] == (
        "active_episode_capacity_rejected"
    )
    assert rejected["scanner_prune_observer_episode_id"].startswith("PRUNEBBO-")
    assert (
        rejected_again["scanner_prune_observer_episode_id"]
        == (rejected["scanner_prune_observer_episode_id"])
    )
    assert rejected["runtime_effect"] is False


def test_default_active_capacity_preserves_two_second_anchor_queue_bound() -> None:
    clock = _Clock(_epoch(9, 10))
    collector = PrunedCandidateBBOCollector(
        "TOKEN",
        clock=clock,
        autostart=False,
    )

    schedules = [
        collector.offer(
            _target(f"{index + 1:06d}"),
            reason="general_slot_limit",
            scan_generation_id="SCANGEN-CAPACITY",
            scan_rank=index + 1,
            ranked_candidate_count=9,
            venue_fields=_venue(),
        )
        for index in range(9)
    ]

    assert all(
        item["scanner_prune_observer_schedule_status"] == "new_episode_scheduled"
        for item in schedules[:8]
    )
    assert schedules[8]["scanner_prune_observer_schedule_status"] == (
        "active_episode_capacity_rejected"
    )
    assert schedules[7]["scanner_prune_observer_max_active_episodes"] == 8


def test_collector_enforces_process_daily_budget_and_minimum_interval() -> None:
    clock = _Clock(_epoch(9, 10))
    collector = PrunedCandidateBBOCollector(
        "TOKEN",
        fetch_quote=lambda _token, request_code, **_kwargs: {
            "source": "ka10004_rest_orderbook",
            "stock_code": request_code[:6],
            "request_code": request_code,
            "rest_received_ts": clock.value,
            "best_bid": 100,
            "best_ask": 101,
        },
        emit_event=lambda *_args, **_kwargs: None,
        clock=clock,
        autostart=False,
        max_active_episodes=2,
        max_daily_requests=10,
    )
    first = collector.offer(
        _target("005930"),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-1",
        scan_rank=1,
        ranked_candidate_count=2,
        venue_fields=_venue(),
    )
    rejected = collector.offer(
        _target("000660"),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-1",
        scan_rank=2,
        ranked_candidate_count=2,
        venue_fields=_venue(),
    )

    assert first["scanner_prune_observer_scheduled_sample_count"] == 10
    assert rejected["scanner_prune_observer_schedule_status"] == (
        "daily_request_budget_rejected"
    )
    assert collector.run_due_once(now_epoch=clock.value) is True

    pacing = PrunedCandidateBBOCollector(
        "TOKEN",
        fetch_quote=lambda _token, request_code, **_kwargs: {
            "source": "ka10004_rest_orderbook",
            "stock_code": request_code[:6],
            "request_code": request_code,
            "rest_received_ts": clock.value,
            "best_bid": 100,
            "best_ask": 101,
        },
        emit_event=lambda *_args, **_kwargs: None,
        clock=clock,
        autostart=False,
        max_active_episodes=2,
        max_daily_requests=20,
    )
    for rank, code in enumerate(("005930", "000660"), start=1):
        pacing.offer(
            _target(code),
            reason="general_slot_limit",
            scan_generation_id="SCANGEN-PACE",
            scan_rank=rank,
            ranked_candidate_count=2,
            venue_fields=_venue(),
        )
    assert pacing.run_due_once(now_epoch=clock.value) is True
    assert pacing.run_due_once(now_epoch=clock.value + 0.1) is False
    clock.value += 0.25
    assert pacing.run_due_once(now_epoch=clock.value) is True


def test_collector_records_route_mismatch_as_gap_without_bbo() -> None:
    clock = _Clock(_epoch(9, 10))
    emitted: list[dict] = []

    def fetch(_token, _request_code, **_kwargs):
        return {
            "source": "ka10004_rest_orderbook",
            "stock_code": "005930",
            "request_code": "005930_NX",
            "rest_received_ts": clock.value,
            "best_bid": 70000,
            "best_ask": 70100,
        }

    collector = PrunedCandidateBBOCollector(
        "TOKEN",
        fetch_quote=fetch,
        emit_event=lambda *args, **kwargs: emitted.append(kwargs["fields"]),
        clock=clock,
        autostart=False,
    )
    collector.offer(
        _target(),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-1",
        scan_rank=1,
        ranked_candidate_count=1,
        venue_fields=_venue(),
    )

    assert collector.run_due_once(now_epoch=clock.value) is True
    assert emitted[0]["scanner_prune_observer_status"] == "source_quality_gap"
    assert emitted[0]["scanner_prune_observer_gap_reason"] == (
        "ka10004_exact_request_route_mismatch"
    )
    assert emitted[0]["scanner_prune_observer_best_bid"] is None
    assert emitted[0]["scanner_prune_observer_best_ask"] is None


def test_collector_surfaces_structured_receipt_failure_in_health(monkeypatch) -> None:
    clock = _Clock(_epoch(9, 10))
    logged: list[str] = []
    monkeypatch.setattr(collector_mod, "log_error", logged.append)
    collector = PrunedCandidateBBOCollector(
        "TOKEN",
        fetch_quote=lambda _token, request_code, **_kwargs: {
            "source": "ka10004_rest_orderbook",
            "stock_code": "005930",
            "request_code": request_code,
            "rest_received_ts": clock.value,
            "best_bid": 70000,
            "best_ask": 70100,
        },
        emit_event=lambda *_args, **_kwargs: {"structured_append_succeeded": False},
        clock=clock,
        autostart=False,
    )
    collector.offer(
        _target(),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-1",
        scan_rank=1,
        ranked_candidate_count=1,
        venue_fields=_venue(),
    )

    assert collector.run_due_once(now_epoch=clock.value) is True
    reused = collector.offer(
        _target(),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-2",
        scan_rank=1,
        ranked_candidate_count=1,
        venue_fields=_venue(),
        observed_epoch=clock.value + 1.0,
    )
    assert reused["scanner_prune_observer_receipt_emit_failure_count"] == 1
    assert len(logged) == 1
    assert "structured_append_not_succeeded" in logged[0]


def test_unexpected_sample_failure_releases_terminal_episode_capacity(
    monkeypatch,
) -> None:
    clock = _Clock(_epoch(15, 29, 59))
    logged: list[str] = []
    emitted: list[dict] = []
    monkeypatch.setattr(collector_mod, "log_error", logged.append)
    collector = PrunedCandidateBBOCollector(
        "TOKEN",
        emit_event=lambda *_args, **kwargs: emitted.append(kwargs["fields"]),
        clock=clock,
        autostart=False,
        max_active_episodes=1,
        max_daily_requests=2,
    )
    collector.offer(
        _target("005930"),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-1",
        scan_rank=1,
        ranked_candidate_count=2,
        venue_fields=_venue(),
    )

    def fail_sample(*_args, **_kwargs):
        raise RuntimeError("unexpected sample failure")

    monkeypatch.setattr(collector, "_collect_and_emit", fail_sample)
    assert collector.run_due_once(now_epoch=clock.value) is True
    clock.value += 0.5
    next_schedule = collector.offer(
        _target("000660"),
        reason="general_slot_limit",
        scan_generation_id="SCANGEN-2",
        scan_rank=2,
        ranked_candidate_count=2,
        venue_fields=_venue(),
    )

    assert next_schedule["scanner_prune_observer_schedule_status"] == (
        "new_episode_scheduled"
    )
    assert next_schedule["scanner_prune_observer_worker_error_count"] == 1
    assert next_schedule["scanner_prune_observer_request_gap_count"] == 1
    assert len(emitted) == 1
    assert emitted[0]["scanner_prune_observer_status"] == "source_quality_gap"
    assert emitted[0]["scanner_prune_observer_gap_reason"] == (
        "unexpected_collector_failure:RuntimeError"
    )
    assert (
        emitted[0]["scanner_prune_observer_request_started_epoch"] == clock.value - 0.5
    )
    assert (
        emitted[0]["scanner_prune_observer_request_completed_epoch"]
        == clock.value - 0.5
    )
    assert emitted[0]["scanner_prune_observer_schedule_lag_sec"] == 0.0
    assert emitted[0]["scanner_prune_observer_route_match"] is False
    assert emitted[0]["scanner_prune_observer_response_request_code"] == (
        "absent_unexpected_collector_failure"
    )
    assert emitted[0]["scanner_prune_observer_best_bid"] is None
    assert emitted[0]["runtime_effect"] is False
    assert "error=RuntimeError" in logged[0]
    assert "fallback_receipt_emitted=true" in logged[0]
