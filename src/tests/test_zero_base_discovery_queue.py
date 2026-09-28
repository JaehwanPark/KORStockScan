from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.scanners.zero_base_discovery_queue import DiscoveryQueue


DAY = "2026-09-28"
T0 = datetime(2026, 9, 28, 9, 10, tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
HASH_A = "a" * 64
HASH_B = "b" * 64


def _observe(queue, code, *, route="krx_only", epoch=T0, digest=HASH_A):
    return queue.observe(
        code=code,
        route=route,
        observed_epoch=epoch,
        source_sha256=digest,
        source_scope="observed_panel",
        received_epoch=epoch + 1,
    )


def test_unseen_candidates_rotate_and_recheck_does_not_starve_them():
    queue = DiscoveryQueue(DAY)
    for code in ("000001", "000002", "000003"):
        assert _observe(queue, code) == "queued"
    first = queue.claim(now_epoch=T0 + 2, limit=1)
    assert [row["code"] for row in first] == ["000001"]
    assert queue.resolve(first[0], result="assessed", machine_action="RECHECK", next_due_epoch=T0 + 2)
    assert [row["code"] for row in queue.claim(now_epoch=T0 + 3, limit=1)] == ["000002"]
    assert [row["code"] for row in queue.claim(now_epoch=T0 + 4, limit=1)] == ["000003"]
    assert [row["code"] for row in queue.claim(now_epoch=T0 + 5, limit=1)] == ["000001"]
    assert queue.claim(now_epoch=T0 + 6, limit=1) == []  # prior claim is in flight


def test_exact_source_generation_and_route_block_stale_resolution():
    queue = DiscoveryQueue(DAY)
    assert _observe(queue, "000001") == "queued"
    claim = queue.claim(now_epoch=T0 + 2, limit=1)[0]
    assert _observe(queue, "000001", epoch=T0 + 3, digest=HASH_B) == "updated"
    assert not queue.resolve(claim, result="assessed", machine_action="ENTER_NOW", next_due_epoch=T0 + 30)
    assert _observe(queue, "000001", route="nxt_only") == "queued"
    assert _observe(queue, "000001", epoch=T0 + 3, digest=HASH_A) == "source_generation_conflict"
    assert len(queue.snapshot()["candidates"]) == 2


def test_source_gap_is_not_machine_block_and_restart_reclaims_inflight():
    queue = DiscoveryQueue(DAY)
    _observe(queue, "000001")
    claim = queue.claim(now_epoch=T0 + 2, limit=1)[0]
    with pytest.raises(ValueError):
        queue.resolve(claim, result="source_unavailable", machine_action="BLOCK", next_due_epoch=T0 + 30)
    assert queue.resolve(claim, result="source_unavailable", next_due_epoch=T0 + 30)
    assert queue.snapshot()["candidates"][0]["machine_action"] == ""
    assert queue.claim(now_epoch=T0 + 29, limit=1) == []
    second = queue.claim(now_epoch=T0 + 30, limit=1)[0]
    restored = DiscoveryQueue.restore(queue.snapshot(), session_date=DAY)
    retry = restored.claim(now_epoch=T0 + 31, limit=1)[0]
    assert retry["code"] == second["code"]
    assert retry["claim_count"] == second["claim_count"] + 1
    assert not restored.resolve(second, result="assessed", machine_action="ENTER_NOW", next_due_epoch=T0 + 40)
    with pytest.raises(ValueError):
        DiscoveryQueue.restore(queue.snapshot(), session_date="2026-09-29")


def test_invalid_or_cross_day_source_cannot_enter_queue():
    queue = DiscoveryQueue(DAY)
    assert _observe(queue, "000001", route="unknown") == "route_unknown"
    assert _observe(queue, "000001", epoch=T0 - 86400) == "source_date_mismatch"
    assert queue.observe(
        code="000001",
        route="krx_only",
        observed_epoch=T0,
        source_sha256=HASH_A,
        source_scope="whole_market",
        received_epoch=T0 + 1,
    ) == "source_scope_unknown"
    assert queue.snapshot()["candidates"] == []
