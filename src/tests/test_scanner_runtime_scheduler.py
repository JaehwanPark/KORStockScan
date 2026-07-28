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


def test_same_promotion_with_same_provenance_coalesces_without_new_revision():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    first = _register(scheduler)
    generation = first.item.generation

    duplicate = _register(scheduler, attach_epoch=102.0)

    assert duplicate.action == "generation_coalesced"
    assert duplicate.reason == "same_promotion_already_registered"
    assert duplicate.item.generation == generation
    assert duplicate.superseded_work_ids == ()
    assert scheduler.current_generation("000001") == generation
    assert duplicate.fields["scanner_duplicate_provenance_match"] is True


def test_same_promotion_coalesce_preserves_inflight_work_identity():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    first = _register(scheduler)
    dispatched = scheduler.next_decision(now_epoch=101.1)

    duplicate = _register(scheduler, attach_epoch=102.0)

    assert duplicate.action == "generation_coalesced"
    assert duplicate.item == dispatched.item
    assert scheduler.is_current(first.item.generation) is True
    completed = scheduler.complete(
        dispatched.item,
        completed_epoch=102.1,
        outcome="pass",
    )
    assert completed.action == "completed"


def test_same_promotion_with_conflicting_provenance_invalidates_fail_closed():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    first = _register(scheduler)
    generation = first.item.generation

    conflict = scheduler.register_generation(
        code="000001",
        promotion_id="PROMO-1",
        record_id=1,
        venue="KRX",
        promotion_epoch=100.0,
        attach_epoch=102.0,
        observed_price=10_100,
        source_signature="VALUE_TOP,VOLUME_SURGE_POSITIVE",
    )

    assert conflict.action == "generation_rejected"
    assert conflict.reason == "same_promotion_provenance_conflict"
    assert any(
        work_id.startswith(generation.generation_id)
        for work_id in conflict.superseded_work_ids
    )
    assert conflict.fields["scanner_duplicate_conflict_fields"] == "observed_price"
    assert scheduler.current_generation("000001") is None
    assert scheduler.snapshot_metrics(now_epoch=102.0)["scheduler_queue_depth"] == 0

    quarantined = _register(scheduler, attach_epoch=103.0)
    assert quarantined.action == "generation_rejected"
    assert quarantined.reason == "promotion_provenance_conflict_quarantined"
    assert scheduler.current_generation("000001") is None

    fresh = _register(
        scheduler,
        promotion_id="PROMO-2",
        promotion_epoch=103.5,
        attach_epoch=104.0,
    )
    assert fresh.action == "generation_registered"
    assert scheduler.current_generation("000001") == fresh.item.generation


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


def test_scheduler_park_discards_hot_work_but_retains_generation_provenance():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    registered = _register(scheduler)
    generation = registered.item.generation
    initial = scheduler.next_decision(now_epoch=101.1)
    scheduler.complete(initial.item, completed_epoch=101.2, outcome="pass")
    heavy = scheduler.enqueue(
        generation,
        lane=ScannerLane.HEAVY_EVAL,
        owner="eligible_precheck_heavy_eval",
        enqueued_epoch=101.2,
    )
    dispatched_heavy = scheduler.next_decision(now_epoch=101.3)
    assert dispatched_heavy.item == heavy.item
    assert dispatched_heavy.fields["attach_to_heavy_dispatch_sec"] == 0.3

    parked = scheduler.park(
        generation,
        now_epoch=102.0,
        reason="heavy_eval_completed_generation_warm_parked",
    )

    assert parked.action == "generation_parked"
    assert parked.superseded_work_ids
    assert scheduler.current_generation("000001") == generation
    assert scheduler.snapshot_metrics(now_epoch=102.0)["scheduler_queue_depth"] == 0
    assert scheduler.next_decision(now_epoch=102.0) is None
    late = scheduler.complete(
        dispatched_heavy.item,
        completed_epoch=102.1,
        outcome="late_worker_result",
    )
    assert late.action == "parked_result"
    assert late.fields["result_current_generation"] is False

    recheck = scheduler.enqueue(
        generation,
        lane=ScannerLane.FAST_PRECHECK,
        owner="explicit_bounded_recheck",
        enqueued_epoch=103.0,
        recheck_evidence_key="material-evidence-v2",
    )
    assert recheck.action == "enqueued"
    assert scheduler.next_decision(now_epoch=103.1).item == recheck.item


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


def test_initial_precheck_is_retained_when_recheck_arrives_before_dispatch():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    registered = _register(scheduler, attach_epoch=100.0, promotion_epoch=99.0)
    generation = registered.item.generation

    retained = scheduler.enqueue(
        generation,
        lane=ScannerLane.FAST_PRECHECK,
        owner="ws_gap_recovery_after_precheck",
        enqueued_epoch=101.0,
        recheck_evidence_key="curr=100",
    )

    assert retained.action == "coalesced"
    assert retained.reason == "initial_fast_precheck_retained"
    assert retained.item.precheck_phase == "initial"
    assert retained.item.deadline_epoch == 110.0

    dispatched = scheduler.next_decision(now_epoch=101.1)
    assert dispatched.action == "dispatch"
    assert dispatched.item.precheck_phase == "initial"
    assert dispatched.fields["attach_to_first_precheck_sec"] == 1.1


def test_same_evidence_fast_recheck_is_rate_coalesced_after_initial_dispatch():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    registered = _register(scheduler, attach_epoch=100.0, promotion_epoch=99.0)
    generation = registered.item.generation
    initial = scheduler.next_decision(now_epoch=100.1)
    scheduler.complete(initial.item, completed_epoch=100.2, outcome="pass")

    first = scheduler.enqueue(
        generation,
        lane=ScannerLane.FAST_PRECHECK,
        owner="budget_retention_fresh_recheck",
        enqueued_epoch=101.0,
        recheck_evidence_key="curr=100|best_bid=99",
    )
    repeated = scheduler.enqueue(
        generation,
        lane=ScannerLane.FAST_PRECHECK,
        owner="budget_retention_fresh_recheck",
        enqueued_epoch=101.5,
        recheck_evidence_key="curr=100|best_bid=99",
    )
    changed = scheduler.enqueue(
        generation,
        lane=ScannerLane.FAST_PRECHECK,
        owner="budget_retention_fresh_recheck",
        enqueued_epoch=101.6,
        recheck_evidence_key="curr=101|best_bid=100",
    )

    assert first.action == "enqueued"
    assert repeated.action == "coalesced"
    assert repeated.reason == "same_generation_fast_recheck_min_interval"
    assert changed.action == "enqueued"
    assert changed.item.recheck_evidence_key == "curr=101|best_bid=100"


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
    scheduler.complete(
        first.item, completed_epoch=100.2, outcome="source_quality_blocked"
    )
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


def test_initial_precheck_is_reserved_ahead_of_recovery_and_heavy_work():
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
        lane=ScannerLane.RECOVERY,
        owner="old_recovery",
        enqueued_epoch=100.2,
        deadline_epoch=104.0,
    )
    scheduler.enqueue(
        observed.item.generation,
        lane=ScannerLane.HEAVY_EVAL,
        owner="old_heavy",
        enqueued_epoch=100.3,
        deadline_epoch=104.5,
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
    assert selected.item.lane is ScannerLane.FAST_PRECHECK
    assert selected.reason == "earliest_deadline_first"


def test_claim_noncritical_lane_yields_to_pending_initial_precheck():
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
        lane=ScannerLane.RECOVERY,
        owner="old_recovery",
        enqueued_epoch=100.2,
        deadline_epoch=104.0,
    )
    newcomer = _register(
        scheduler,
        code="000002",
        promotion_id="PROMO-NEW",
        attach_epoch=101.0,
        promotion_epoch=100.5,
    )

    deferred = scheduler.claim(
        observed.item.generation,
        lane=ScannerLane.RECOVERY,
        now_epoch=101.1,
    )

    assert deferred.action == "not_next"
    assert deferred.reason == "initial_fast_precheck_reservation"
    assert deferred.item.generation == newcomer.item.generation


def test_safety_and_commit_remain_ahead_of_initial_precheck_reservation():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    critical = _register(
        scheduler,
        code="000001",
        promotion_id="PROMO-CRITICAL",
        attach_epoch=100.0,
        promotion_epoch=99.0,
    )
    first = scheduler.next_decision(now_epoch=100.1)
    scheduler.complete(first.item, completed_epoch=100.2, outcome="pass")
    scheduler.enqueue(
        critical.item.generation,
        lane=ScannerLane.COMMIT,
        owner="completed_async_result",
        enqueued_epoch=100.2,
        deadline_epoch=120.0,
    )
    scheduler.enqueue(
        critical.item.generation,
        lane=ScannerLane.SAFETY,
        owner="receipt_safety",
        enqueued_epoch=100.3,
        deadline_epoch=120.0,
    )
    newcomer = _register(
        scheduler,
        code="000002",
        promotion_id="PROMO-NEW",
        attach_epoch=101.0,
        promotion_epoch=100.5,
    )

    safety = scheduler.next_decision(now_epoch=101.1)
    scheduler.complete(safety.item, completed_epoch=101.2, outcome="safe")
    commit = scheduler.next_decision(now_epoch=101.3)
    scheduler.complete(commit.item, completed_epoch=101.4, outcome="committed")
    initial = scheduler.next_decision(now_epoch=101.5)

    assert safety.item.lane is ScannerLane.SAFETY
    assert commit.item.lane is ScannerLane.COMMIT
    assert initial.item.generation == newcomer.item.generation
    assert initial.item.lane is ScannerLane.FAST_PRECHECK


def test_claim_noncritical_lane_yields_to_critical_before_initial_precheck():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    critical = _register(
        scheduler,
        code="000001",
        promotion_id="PROMO-CRITICAL",
        attach_epoch=100.0,
        promotion_epoch=99.0,
    )
    first = scheduler.next_decision(now_epoch=100.1)
    scheduler.complete(first.item, completed_epoch=100.2, outcome="pass")
    scheduler.enqueue(
        critical.item.generation,
        lane=ScannerLane.RECOVERY,
        owner="recovery",
        enqueued_epoch=100.2,
    )
    scheduler.enqueue(
        critical.item.generation,
        lane=ScannerLane.COMMIT,
        owner="completed_async_result",
        enqueued_epoch=100.3,
        deadline_epoch=120.0,
    )
    _register(
        scheduler,
        code="000002",
        promotion_id="PROMO-NEW",
        attach_epoch=101.0,
        promotion_epoch=100.5,
    )

    deferred = scheduler.claim(
        critical.item.generation,
        lane=ScannerLane.RECOVERY,
        now_epoch=101.1,
    )

    assert deferred.action == "not_next"
    assert deferred.reason == "critical_lane_reservation"
    assert deferred.item.lane is ScannerLane.COMMIT


def test_recurring_precheck_and_recovery_use_extended_non_initial_deadlines():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    registered = _register(
        scheduler,
        attach_epoch=100.0,
        promotion_epoch=99.0,
    )
    initial = scheduler.next_decision(now_epoch=100.1)
    assert initial.item.deadline_epoch == 110.0
    scheduler.complete(initial.item, completed_epoch=100.2, outcome="pass")

    recurring = scheduler.enqueue(
        registered.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        owner="recurring",
        enqueued_epoch=101.0,
    )
    recovery = scheduler.enqueue(
        registered.item.generation,
        lane=ScannerLane.RECOVERY,
        owner="recovery",
        enqueued_epoch=101.0,
    )

    assert recurring.item.precheck_phase == "recheck"
    assert recurring.item.deadline_epoch == 131.0
    assert recovery.item.deadline_epoch == 131.0


def test_refreshed_initial_precheck_dispatches_ahead_of_expired_peer():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    _register(
        scheduler,
        code="000001",
        promotion_id="PROMO-EXPIRED",
        attach_epoch=100.0,
        promotion_epoch=99.0,
    )
    refreshed = _register(
        scheduler,
        code="000002",
        promotion_id="PROMO-REFRESHED",
        attach_epoch=100.0,
        promotion_epoch=99.0,
    )

    expired = scheduler.claim(
        refreshed.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        now_epoch=120.0,
    )
    assert expired.action in {"deadline_expired", "not_next"}
    if expired.action == "not_next":
        expired = scheduler.claim(
            expired.item.generation,
            lane=ScannerLane.FAST_PRECHECK,
            now_epoch=120.0,
        )
    assert expired.action == "deadline_expired"

    refreshed_generation = expired.item.generation
    fresh_attempt = scheduler.enqueue(
        refreshed_generation,
        lane=ScannerLane.FAST_PRECHECK,
        owner="fresh_recheck_after_deadline",
        enqueued_epoch=120.0,
        attempt=2,
    )
    dispatched = scheduler.claim(
        refreshed_generation,
        lane=ScannerLane.FAST_PRECHECK,
        now_epoch=120.1,
    )

    assert fresh_attempt.item.precheck_phase == "initial"
    assert dispatched.action == "dispatch"
    assert dispatched.item.generation == refreshed_generation


def test_unexpired_initial_peer_still_keeps_edf_priority():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    earlier = _register(
        scheduler,
        code="000001",
        promotion_id="PROMO-EARLIER",
        attach_epoch=100.0,
        promotion_epoch=99.0,
    )
    later = _register(
        scheduler,
        code="000002",
        promotion_id="PROMO-LATER",
        attach_epoch=101.0,
        promotion_epoch=100.0,
    )

    deferred = scheduler.claim(
        later.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        now_epoch=102.0,
    )

    assert deferred.action == "not_next"
    assert deferred.item.generation == earlier.item.generation


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


def test_expired_requested_recheck_closes_despite_fresh_recurring_peer():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    expired = _register(
        scheduler,
        code="000001",
        promotion_id="PROMO-EXPIRED",
        attach_epoch=100.0,
        promotion_epoch=99.0,
    )
    expired_initial = scheduler.claim(
        expired.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        now_epoch=100.1,
    )
    scheduler.complete(expired_initial.item, completed_epoch=100.2, outcome="pass")
    expired_recheck = scheduler.enqueue(
        expired.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        owner="old_recurring_recheck",
        enqueued_epoch=100.2,
    )

    fresh = _register(
        scheduler,
        code="000002",
        promotion_id="PROMO-FRESH",
        attach_epoch=139.0,
        promotion_epoch=138.5,
    )
    fresh_initial = scheduler.claim(
        fresh.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        now_epoch=139.1,
    )
    scheduler.complete(fresh_initial.item, completed_epoch=139.2, outcome="pass")
    fresh_recheck = scheduler.enqueue(
        fresh.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        owner="post_heavy_eval_fresh_recheck",
        enqueued_epoch=139.2,
    )

    decision = scheduler.claim(
        expired.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        now_epoch=140.0,
    )

    assert expired_recheck.item.deadline_epoch < 140.0
    assert fresh_recheck.item.deadline_epoch > 140.0
    assert decision.action == "deadline_expired"
    assert decision.item == expired_recheck.item
    fresh_decision = scheduler.claim(
        fresh.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        now_epoch=140.0,
    )
    assert fresh_decision.action == "dispatch"
    assert fresh_decision.item == fresh_recheck.item


def test_completed_requester_reports_missing_instead_of_yielding_to_fresh_peer():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    requester = _register(
        scheduler,
        code="000001",
        promotion_id="PROMO-COMPLETED",
        attach_epoch=100.0,
        promotion_epoch=99.0,
    )
    requester_work = scheduler.claim(
        requester.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        now_epoch=100.1,
    )
    scheduler.complete(
        requester_work.item,
        completed_epoch=100.2,
        outcome="pass",
    )

    peer = _register(
        scheduler,
        code="000002",
        promotion_id="PROMO-PEER",
        attach_epoch=100.3,
        promotion_epoch=100.2,
    )
    decision = scheduler.claim(
        requester.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        now_epoch=100.4,
    )

    assert peer.item.deadline_epoch > 100.4
    assert decision.action == "missing"
    assert decision.reason == "generation_lane_not_enqueued"
    assert decision.item is None


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

    assert all(decision.item.precheck_phase == "initial" for decision in dispatched)
    assert {decision.item.generation.generation_id for decision in dispatched} == {
        newcomer.item.generation.generation_id for newcomer in newcomers
    }
    assert (
        max(decision.fields["attach_to_first_precheck_sec"] for decision in dispatched)
        <= 10.0
    )

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
