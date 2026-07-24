from __future__ import annotations

from src.engine.scalping.scanner_runtime_scheduler import (
    SCANNER_DEADLINE_SCHEDULER_VERSION,
    ScannerLane,
    ScannerPromotionEnvelope,
    ScannerPromotionInbox,
    ScannerRuntimeScheduler,
    normalize_scanner_scheduler_mode,
    parse_scanner_scheduler_venues,
)


def _register(
    scheduler: ScannerRuntimeScheduler,
    *,
    code: str = "000001",
    promotion_id: str = "PROMO-1",
    attach_epoch: float = 101.0,
    promotion_epoch: float = 100.0,
):
    return scheduler.register_generation(
        code=code,
        promotion_id=promotion_id,
        record_id=1,
        venue="KRX",
        promotion_epoch=promotion_epoch,
        attach_epoch=attach_epoch,
        observed_price=10_000,
        source_signature="VALUE_TOP,VOLUME_SURGE_POSITIVE",
    )


def test_scheduler_mode_and_venue_parsing_fail_closed():
    assert normalize_scanner_scheduler_mode("deadline_v1") == "deadline_v1"
    assert normalize_scanner_scheduler_mode("unknown") == "legacy"
    assert parse_scanner_scheduler_venues("KRX,premarket,nxt,unknown") == frozenset(
        {"KRX", "PREMARKET_KRX_LIKE", "NXT"}
    )


def test_promotion_inbox_coalesces_latest_generation_and_enforces_cap():
    inbox = ScannerPromotionInbox(max_active=2)
    first = ScannerPromotionEnvelope.from_payload(
        {"code": "000001", "scanner_promotion_id": "PROMO-1"},
        enqueued_epoch=100.0,
    )
    latest = ScannerPromotionEnvelope.from_payload(
        {"code": "000001", "scanner_promotion_id": "PROMO-2"},
        enqueued_epoch=101.0,
    )
    second = ScannerPromotionEnvelope.from_payload(
        {"code": "000002", "scanner_promotion_id": "PROMO-3"},
        enqueued_epoch=102.0,
    )
    rejected = ScannerPromotionEnvelope.from_payload(
        {"code": "000003", "scanner_promotion_id": "PROMO-4"},
        enqueued_epoch=103.0,
    )

    assert inbox.put(first).accepted is True
    coalesced = inbox.put(latest)
    assert coalesced.accepted is True
    assert coalesced.superseded_envelope == first
    assert inbox.put(second).accepted is True
    assert inbox.put(rejected).accepted is False
    assert len(inbox) == 2
    assert inbox.pending_for("000001") == latest
    assert inbox.get_nowait().payload["scanner_promotion_id"] == "PROMO-2"
    assert inbox.pending_for("000001") is None
    assert inbox.get_nowait().payload["scanner_promotion_id"] == "PROMO-3"


def test_new_generation_supersedes_queued_and_inflight_work():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    first = _register(scheduler)
    first_generation = first.item.generation
    dispatched = scheduler.next_decision(now_epoch=101.1)
    assert dispatched.action == "dispatch"
    assert dispatched.item.generation == first_generation

    second = _register(
        scheduler,
        promotion_id="PROMO-2",
        attach_epoch=102.0,
        promotion_epoch=101.5,
    )
    assert dispatched.item.work_id in second.superseded_work_ids
    assert scheduler.is_current(first_generation) is False
    assert scheduler.is_current(second.item.generation) is True

    late = scheduler.complete(
        dispatched.item,
        completed_epoch=103.0,
        outcome="eligible_for_heavy_entry_eval",
    )
    assert late.action == "superseded_result"
    assert late.fields["result_current_generation"] is False


def test_scheduler_uses_absolute_deadline_then_lane_tie_priority():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    registered = _register(scheduler)
    generation = registered.item.generation

    # Remove the automatically queued precheck first.
    precheck = scheduler.next_decision(now_epoch=101.1)
    scheduler.complete(precheck.item, completed_epoch=101.2, outcome="pass")
    scheduler.enqueue(
        generation,
        lane=ScannerLane.HEAVY_EVAL,
        owner="test",
        enqueued_epoch=102.0,
        deadline_epoch=110.0,
    )
    scheduler.enqueue(
        generation,
        lane=ScannerLane.COMMIT,
        owner="test",
        enqueued_epoch=103.0,
        deadline_epoch=110.0,
    )

    selected = scheduler.next_decision(now_epoch=104.0)
    assert selected.item.lane is ScannerLane.COMMIT


def test_scheduler_expired_work_is_explicit_and_never_inflight():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    _register(scheduler)
    expired = scheduler.next_decision(now_epoch=112.0)

    assert expired.action == "deadline_expired"
    assert expired.reason == "work_deadline_elapsed_before_dispatch"
    assert expired.fields["deadline_overrun_sec"] == 1.0
    assert scheduler.snapshot_metrics(now_epoch=112.0)["scheduler_in_flight_count"] == 0


def test_same_generation_lane_enqueue_coalesces_latest_deadline():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    registered = _register(scheduler)
    generation = registered.item.generation
    initial = scheduler.next_decision(now_epoch=101.1)
    scheduler.complete(initial.item, completed_epoch=101.2, outcome="pass")

    scheduler.enqueue(
        generation,
        lane=ScannerLane.RECOVERY,
        owner="first",
        enqueued_epoch=102.0,
        deadline_epoch=106.0,
    )
    scheduler.enqueue(
        generation,
        lane=ScannerLane.RECOVERY,
        owner="latest",
        enqueued_epoch=103.0,
        deadline_epoch=107.0,
    )
    metrics = scheduler.snapshot_metrics(now_epoch=103.0)
    assert metrics["scheduler_queue_depth"] == 1

    decision = scheduler.next_decision(now_epoch=103.5)
    assert decision.item.owner == "latest"
    assert decision.item.deadline_epoch == 107.0


def test_claim_path_does_not_accumulate_stale_heap_entries():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    registered = _register(scheduler)
    generation = registered.item.generation

    for attempt in range(1, 101):
        claimed = scheduler.claim(
            generation,
            lane=ScannerLane.FAST_PRECHECK,
            now_epoch=101.0 + attempt,
        )
        assert claimed.action in {"dispatch", "deadline_expired"}
        if claimed.action == "dispatch":
            scheduler.complete(
                claimed.item,
                completed_epoch=101.1 + attempt,
                outcome="pass",
            )
        scheduler.enqueue(
            generation,
            lane=ScannerLane.FAST_PRECHECK,
            owner="repeat",
            enqueued_epoch=101.2 + attempt,
            attempt=attempt + 1,
        )

    metrics = scheduler.snapshot_metrics(now_epoch=202.0)
    assert metrics["scheduler_queue_depth"] == 1
    assert metrics["scheduler_heap_depth"] == 1


def test_claim_respects_earliest_deadline_within_lane():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    later = _register(
        scheduler,
        code="000001",
        promotion_id="PROMO-LATER",
        attach_epoch=101.0,
    )
    earlier = _register(
        scheduler,
        code="000002",
        promotion_id="PROMO-EARLIER",
        attach_epoch=100.0,
    )

    deferred = scheduler.claim(
        later.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        now_epoch=101.1,
    )
    assert deferred.action == "not_next"
    assert deferred.item.generation == earlier.item.generation

    dispatched = scheduler.claim(
        earlier.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        now_epoch=101.1,
    )
    assert dispatched.action == "dispatch"


def test_initial_precheck_precedes_earlier_recurring_recheck():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    observed = _register(
        scheduler,
        code="000001",
        promotion_id="PROMO-OBSERVED",
        attach_epoch=100.0,
        promotion_epoch=99.0,
    )
    first = scheduler.claim(
        observed.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        now_epoch=100.1,
    )
    scheduler.complete(first.item, completed_epoch=100.2, outcome="source_quality_blocked")
    recurring = scheduler.enqueue(
        observed.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        owner="precheck_not_eligible_fresh_recheck",
        enqueued_epoch=100.2,
        deadline_epoch=110.2,
        attempt=2,
    )
    newcomer = _register(
        scheduler,
        code="000002",
        promotion_id="PROMO-NEW",
        attach_epoch=101.0,
        promotion_epoch=100.5,
    )

    reserved = scheduler.claim(
        newcomer.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        now_epoch=101.1,
    )

    assert recurring.item.deadline_epoch < newcomer.item.deadline_epoch
    assert recurring.item.precheck_phase == "recheck"
    assert newcomer.item.precheck_phase == "initial"
    assert reserved.action == "dispatch"
    assert reserved.item.generation == newcomer.item.generation
    assert reserved.fields["scanner_scheduler_precheck_phase"] == "initial"
    assert reserved.fields["attach_to_first_precheck_sec"] == 0.1

    scheduler.complete(reserved.item, completed_epoch=101.2, outcome="pass")
    retry = scheduler.claim(
        observed.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        now_epoch=101.3,
    )
    assert retry.action == "dispatch"
    assert retry.item == recurring.item
    assert retry.fields["scanner_scheduler_precheck_phase"] == "recheck"
    assert "attach_to_first_precheck_sec" not in retry.fields
    assert retry.fields["precheck_recheck_wait_sec"] == 1.1


def test_expired_undispatched_precheck_retry_remains_initial():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    registered = _register(
        scheduler,
        attach_epoch=100.0,
        promotion_epoch=99.0,
    )
    expired = scheduler.claim(
        registered.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        now_epoch=110.1,
    )
    retry = scheduler.enqueue(
        registered.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        owner="fresh_recheck_after_deadline",
        enqueued_epoch=110.1,
        attempt=2,
    )

    assert expired.action == "deadline_expired"
    assert expired.item.precheck_phase == "initial"
    assert retry.item.precheck_phase == "initial"
    assert retry.fields["scanner_scheduler_precheck_phase"] == "initial"


def test_next_decision_reserves_initial_precheck_over_recurring_recheck():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    observed = _register(
        scheduler,
        code="000001",
        promotion_id="PROMO-OBSERVED",
        attach_epoch=100.0,
        promotion_epoch=99.0,
    )
    first = scheduler.next_decision(now_epoch=100.1)
    scheduler.complete(first.item, completed_epoch=100.2, outcome="pass")
    scheduler.enqueue(
        observed.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        owner="post_heavy_eval_fresh_recheck",
        enqueued_epoch=100.2,
        deadline_epoch=110.2,
        attempt=2,
    )
    newcomer = _register(
        scheduler,
        code="000002",
        promotion_id="PROMO-NEW",
        attach_epoch=101.0,
        promotion_epoch=100.5,
    )

    selected = scheduler.next_decision(now_epoch=101.1)

    assert selected.action == "dispatch"
    assert selected.item.generation == newcomer.item.generation
    assert selected.item.precheck_phase == "initial"


def test_recurring_recheck_cannot_consume_sixteen_symbol_first_precheck_budget():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    observed = _register(
        scheduler,
        code="000001",
        promotion_id="PROMO-OBSERVED",
        attach_epoch=100.0,
        promotion_epoch=99.0,
    )
    first = scheduler.next_decision(now_epoch=100.1)
    scheduler.complete(first.item, completed_epoch=100.2, outcome="pass")
    recurring = scheduler.enqueue(
        observed.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        owner="precheck_not_eligible_fresh_recheck",
        enqueued_epoch=100.2,
        deadline_epoch=110.2,
        attempt=2,
    )
    newcomers = [
        _register(
            scheduler,
            code=f"{index:06d}",
            promotion_id=f"PROMO-{index}",
            attach_epoch=101.0,
            promotion_epoch=100.5,
        )
        for index in range(2, 17)
    ]

    dispatched = []
    for offset, newcomer in enumerate(newcomers):
        now_epoch = 101.1 + (offset * 0.5)
        decision = scheduler.next_decision(now_epoch=now_epoch)
        dispatched.append(decision)
        scheduler.complete(
            decision.item,
            completed_epoch=now_epoch + 0.4,
            outcome="pass",
        )

    assert all(
        decision.item.precheck_phase == "initial" for decision in dispatched
    )
    assert {
        decision.item.generation.generation_id for decision in dispatched
    } == {newcomer.item.generation.generation_id for newcomer in newcomers}
    assert max(
        decision.fields["attach_to_first_precheck_sec"] for decision in dispatched
    ) <= 10.0

    after_initials = scheduler.next_decision(now_epoch=108.6)
    assert after_initials.item == recurring.item
    assert after_initials.item.precheck_phase == "recheck"


def test_service_time_excludes_queue_wait():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    _register(scheduler, attach_epoch=100.0)
    dispatched = scheduler.next_decision(now_epoch=101.5)
    completed = scheduler.complete(
        dispatched.item,
        completed_epoch=101.75,
        outcome="pass",
    )

    assert completed.fields["scanner_scheduler_queue_wait_sec"] == 1.5
    assert completed.fields["work_service_sec"] == 0.25


def test_generation_capacity_rejects_without_partial_registration():
    scheduler = ScannerRuntimeScheduler(max_active=1)
    first = _register(scheduler, code="000001")
    rejected = _register(scheduler, code="000002")

    assert first.action == "generation_registered"
    assert rejected.action == "capacity_rejected"
    assert rejected.item is None
    assert scheduler.generation_codes() == frozenset({"000001"})


def test_generation_rejects_missing_or_conflicting_provenance():
    scheduler = ScannerRuntimeScheduler(max_active=4)

    missing_id = scheduler.register_generation(
        code="000001",
        promotion_id="",
        record_id=1,
        venue="KRX",
        promotion_epoch=100.0,
        attach_epoch=101.0,
        observed_price=10_000,
        source_signature="VALUE_TOP",
    )
    attach_before_promotion = scheduler.register_generation(
        code="000002",
        promotion_id="PROMO-2",
        record_id=2,
        venue="KRX",
        promotion_epoch=102.0,
        attach_epoch=101.0,
        observed_price=10_000,
        source_signature="VALUE_TOP",
    )
    unknown_venue = scheduler.register_generation(
        code="000003",
        promotion_id="PROMO-3",
        record_id=3,
        venue="UNKNOWN",
        promotion_epoch=100.0,
        attach_epoch=101.0,
        observed_price=10_000,
        source_signature="VALUE_TOP",
    )

    assert missing_id.action == "generation_rejected"
    assert attach_before_promotion.action == "generation_rejected"
    assert unknown_venue.action == "generation_rejected"
    assert scheduler.generation_codes() == frozenset()


def test_fast_precheck_cannot_follow_more_than_two_blocking_heavy_jobs():
    scheduler = ScannerRuntimeScheduler(max_active=4)
    registrations = [
        _register(
            scheduler,
            code=f"{index:06d}",
            promotion_id=f"PROMO-{index}",
            attach_epoch=100.0,
        )
        for index in range(1, 5)
    ]
    for _ in registrations:
        precheck = scheduler.next_decision(now_epoch=100.1)
        scheduler.complete(precheck.item, completed_epoch=100.2, outcome="pass")

    for registered in registrations[:3]:
        scheduler.enqueue(
            registered.item.generation,
            lane=ScannerLane.HEAVY_EVAL,
            owner="stress",
            enqueued_epoch=101.0,
            deadline_epoch=120.0,
        )
    scheduler.enqueue(
        registrations[3].item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        owner="new_promotion",
        enqueued_epoch=101.0,
        deadline_epoch=130.0,
        attempt=2,
    )

    first = scheduler.next_decision(now_epoch=101.1)
    scheduler.complete(first.item, completed_epoch=106.1, outcome="timeout")
    second = scheduler.next_decision(now_epoch=106.1)
    scheduler.complete(second.item, completed_epoch=111.1, outcome="timeout")
    third = scheduler.next_decision(now_epoch=111.1)

    assert first.item.lane is ScannerLane.HEAVY_EVAL
    assert second.item.lane is ScannerLane.HEAVY_EVAL
    assert third.item.lane is ScannerLane.FAST_PRECHECK


def test_scheduler_generation_provenance_never_reuses_old_price_or_anchor():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    first = _register(scheduler)
    second = scheduler.register_generation(
        code="000001",
        promotion_id="PROMO-2",
        record_id=2,
        venue="NXT",
        promotion_epoch=200.0,
        attach_epoch=201.25,
        observed_price=11_000,
        source_signature="OPEN_TOP",
    )
    generation = second.item.generation

    assert generation.revision == first.item.generation.revision + 1
    assert generation.promotion_id == "PROMO-2"
    assert generation.promotion_epoch == 200.0
    assert generation.attach_epoch == 201.25
    assert generation.observed_price == 11_000
    assert generation.venue == "NXT"
    assert second.fields["promotion_to_attach_sec"] == 1.25
    assert second.fields["scheduler_version"] == SCANNER_DEADLINE_SCHEDULER_VERSION


def test_sixteen_symbol_stress_has_one_latest_precheck_per_symbol():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    for index in range(16):
        _register(
            scheduler,
            code=f"{index + 1:06d}",
            promotion_id=f"PROMO-{index}",
            attach_epoch=100.0,
            promotion_epoch=99.5,
        )

    dispatched = []
    while True:
        decision = scheduler.next_decision(now_epoch=100.1)
        if decision is None:
            break
        dispatched.append(decision)
        scheduler.complete(decision.item, completed_epoch=100.2, outcome="pass")

    assert len(dispatched) == 16
    assert all(item.action == "dispatch" for item in dispatched)
    assert {item.item.generation.code for item in dispatched} == {
        f"{index + 1:06d}" for index in range(16)
    }
    attach_lags = [item.fields["attach_to_first_precheck_sec"] for item in dispatched]
    assert max(attach_lags) <= 5.0
    assert sorted(attach_lags)[14] <= 2.0
