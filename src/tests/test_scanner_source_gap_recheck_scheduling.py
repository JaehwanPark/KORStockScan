from src.engine.scalping.scanner_runtime_scheduler import (
    ScannerLane,
    ScannerRuntimeScheduler,
)


def _register(
    scheduler: ScannerRuntimeScheduler,
    *,
    code: str,
    promotion_id: str,
    promotion_epoch: float,
    attach_epoch: float,
):
    return scheduler.register_generation(
        code=code,
        promotion_id=promotion_id,
        record_id=code,
        venue="KRX",
        promotion_epoch=promotion_epoch,
        attach_epoch=attach_epoch,
        observed_price=10_000,
        source_signature="PRICE_JUMP_START",
    )


def test_low_priority_source_gap_recheck_does_not_head_of_line_block_peer_recheck():
    scheduler = ScannerRuntimeScheduler(max_active=16)
    source_gap = _register(
        scheduler,
        code="000001",
        promotion_id="PROMO-SOURCE-GAP",
        promotion_epoch=99.0,
        attach_epoch=100.0,
    )
    source_initial = scheduler.claim(
        source_gap.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        now_epoch=100.1,
    )
    scheduler.complete(
        source_initial.item,
        completed_epoch=100.2,
        outcome="source_quality_blocked",
    )
    source_recheck = scheduler.enqueue(
        source_gap.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        owner="opening_rotation_source_gap_fresh_0b_recheck",
        enqueued_epoch=105.0,
        priority=-1,
        recheck_evidence_key="source-gap-0b",
    )

    peer = _register(
        scheduler,
        code="000002",
        promotion_id="PROMO-PEER",
        promotion_epoch=104.9,
        attach_epoch=105.1,
    )
    peer_initial = scheduler.claim(
        peer.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        now_epoch=105.2,
    )
    scheduler.complete(
        peer_initial.item,
        completed_epoch=105.3,
        outcome="fresh_consistent",
    )
    peer_recheck = scheduler.enqueue(
        peer.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        owner="ordinary_fresh_evidence_recheck",
        enqueued_epoch=105.3,
        recheck_evidence_key="peer-fresh",
    )

    selected = scheduler.claim(
        peer.item.generation,
        lane=ScannerLane.FAST_PRECHECK,
        now_epoch=105.4,
    )

    assert source_recheck.item.deadline_epoch == 135.0
    assert source_recheck.item.priority == -1
    assert peer_recheck.item.deadline_epoch == 135.3
    assert selected.action == "dispatch"
    assert selected.item == peer_recheck.item
