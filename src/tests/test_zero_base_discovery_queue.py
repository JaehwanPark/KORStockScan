from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.scanners.zero_base_discovery_queue import DiscoveryQueue


DAY = "2026-09-28"
T0 = datetime(2026, 9, 28, 9, 10, tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
HASH_A = "a" * 64
HASH_B = "b" * 64


def _observe(queue, code, *, route="krx_only", market="", epoch=T0, digest=HASH_A,
             volume=0, kind=""):
    return queue.observe(
        code=code,
        route=route,
        observed_epoch=epoch,
        source_sha256=digest,
        source_scope="observed_panel",
        received_epoch=epoch + 1,
        discovery_volume=volume,
        market=market,
        source_kind=kind,
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


def test_same_age_unseen_candidates_use_liquidity_as_tie_breaker():
    queue = DiscoveryQueue(DAY)
    _observe(queue, "000001", volume=10)
    _observe(queue, "000002", volume=100)
    first = queue.claim(now_epoch=T0 + 2, limit=1)
    assert first[0]["code"] == "000002"
    assert first[0]["discovery_volume"] == 100
    assert queue.resolve(first[0], result="source_unavailable", next_due_epoch=T0 + 2)
    assert queue.claim(now_epoch=T0 + 3, limit=1)[0]["code"] == "000001"


def test_fresh_panel_cohorts_rotate_before_one_panel_exhausts_budget():
    queue = DiscoveryQueue(DAY)
    cohorts = (
        ("KOSPI", "krx_only"), ("KOSDAQ", "krx_only"),
        ("KOSPI", "nxt_only"), ("KOSDAQ", "nxt_only"),
    )
    code = 1
    for market, route in cohorts:
        for _ in range(20):
            _observe(queue, f"{code:06d}", market=market, route=route)
            code += 1
    first = queue.claim(now_epoch=T0 + 2, limit=8)
    assert len(first) == 8
    assert {cohort: sum((row["market"], row["route"]) == cohort for row in first)
            for cohort in cohorts} == {cohort: 2 for cohort in cohorts}
    next_four = [queue.claim(now_epoch=T0 + 3 + index, limit=1)[0]
                 for index in range(4)]
    assert {(row["market"], row["route"]) for row in next_four} == set(cohorts)


def test_active_volume_candidates_get_bounded_priority_without_starving_gainers():
    queue = DiscoveryQueue(DAY)
    for index in range(1, 13):
        _observe(queue, f"{index:06d}", market="KOSPI" if index % 2 else "KOSDAQ",
                 route="krx_nxt_integrated", kind="activity")
    for index in range(13, 25):
        _observe(queue, f"{index:06d}", market="KOSPI" if index % 2 else "KOSDAQ",
                 route="krx_nxt_integrated", kind="gainers")

    first = queue.claim(now_epoch=T0 + 2, limit=8)
    assert [row["source_kind"] for row in first] == [
        "activity", "activity", "activity", "gainers",
        "activity", "activity", "activity", "gainers",
    ]
    assert {row["market"] for row in first if row["source_kind"] == "activity"} == {
        "KOSPI", "KOSDAQ",
    }
    assert {row["market"] for row in first if row["source_kind"] == "gainers"} == {
        "KOSPI", "KOSDAQ",
    }
    restored = DiscoveryQueue.restore(queue.snapshot(), session_date=DAY)
    assert {row["source_kind"] for row in restored.snapshot()["candidates"]} == {
        "activity", "gainers",
    }


def test_aftermarket_source_rotation_keeps_a_gainer_claim():
    queue = DiscoveryQueue(DAY)
    for index in range(1, 25):
        _observe(queue, f"{index:06d}", route="krx_nxt_integrated", kind="activity")
    for index in range(25, 33):
        _observe(queue, f"{index:06d}", route="krx_nxt_integrated", kind="gainers")
    first = queue.claim(
        now_epoch=T0 + 2, limit=8, activity_claims_per_gainer=7,
    )
    assert [row["source_kind"] for row in first] == ["activity"] * 7 + ["gainers"]
    second = DiscoveryQueue.restore(queue.snapshot(), session_date=DAY).claim(
        now_epoch=T0 + 10, limit=8, activity_claims_per_gainer=7,
    )
    assert [row["source_kind"] for row in second] == ["activity"] * 7 + ["gainers"]
    with pytest.raises(ValueError):
        queue.claim(now_epoch=T0 + 11, limit=1, activity_claims_per_gainer=0)


def test_single_claim_calls_keep_source_rotation_after_restart():
    queue = DiscoveryQueue(DAY)
    for index in range(1, 9):
        _observe(queue, f"{index:06d}", kind="activity")
    for index in range(9, 17):
        _observe(queue, f"{index:06d}", kind="gainers")
    first = [queue.claim(now_epoch=T0 + 2 + index, limit=1)[0]["source_kind"]
             for index in range(4)]
    assert first == ["activity", "activity", "activity", "gainers"]
    restored = DiscoveryQueue.restore(queue.snapshot(), session_date=DAY)
    second = [restored.claim(now_epoch=T0 + 10 + index, limit=1)[0]["source_kind"]
              for index in range(4)]
    assert second == first


def test_exact_source_generation_and_route_block_stale_resolution():
    queue = DiscoveryQueue(DAY)
    assert _observe(queue, "000001") == "queued"
    claim = queue.claim(now_epoch=T0 + 2, limit=1)[0]
    assert _observe(queue, "000001", epoch=T0 + 3, digest=HASH_B) == "updated"
    assert queue.claim(now_epoch=T0 + 4, limit=1) == []
    assert queue.resolve(claim, result="assessed", machine_action="ENTER_NOW", next_due_epoch=T0 + 30)
    assert not queue.resolve(claim, result="assessed", machine_action="ENTER_NOW", next_due_epoch=T0 + 30)
    assert queue.claim(now_epoch=T0 + 5, limit=1)[0]["source_sha256"] == HASH_B
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


def test_refreshed_inflight_claim_timeout_still_rejects_late_result():
    queue = DiscoveryQueue(DAY)
    _observe(queue, "000001")
    claim = queue.claim(now_epoch=T0 + 2, limit=1)[0]
    assert _observe(queue, "000001", epoch=T0 + 3, digest=HASH_B) == "updated"
    restored = DiscoveryQueue.restore(queue.snapshot(), session_date=DAY)
    assert not restored.resolve(
        claim, result="assessed", machine_action="ENTER_NOW", next_due_epoch=T0 + 30,
    )
    refreshed = restored.claim(now_epoch=T0 + 7, limit=1)[0]
    assert refreshed["source_sha256"] == HASH_B
    assert restored.abandon_expired_claims(now_epoch=T0 + 68, timeout_sec=60) == 1
    assert not restored.resolve(
        refreshed, result="assessed", machine_action="ENTER_NOW", next_due_epoch=T0 + 80,
    )


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


def test_stale_observation_cannot_consume_probe_budget_until_refreshed():
    queue = DiscoveryQueue(DAY)
    assert _observe(queue, "000001") == "queued"
    assert queue.claim(
        now_epoch=T0 + 121, limit=8, max_observation_age_sec=120,
    ) == []
    assert queue.stale_candidate_count(now_epoch=T0 + 121, max_observation_age_sec=120) == 1
    assert _observe(queue, "000001", epoch=T0 + 122, digest=HASH_B) == "updated"
    assert [row["code"] for row in queue.claim(
        now_epoch=T0 + 123, limit=8, max_observation_age_sec=120,
    )] == ["000001"]
