from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.scanners.zero_base_discovery_queue import DiscoveryQueue

DAY = "2026-09-28"
T0 = datetime(2026, 9, 28, 9, 10, tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
HASH_A = "a" * 64
HASH_B = "b" * 64


def _observe(
    queue,
    code,
    *,
    route="krx_only",
    market="",
    epoch=T0,
    digest=HASH_A,
    volume=0,
    kind="",
):
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
    assert queue.resolve(
        first[0], result="assessed", machine_action="RECHECK", next_due_epoch=T0 + 2
    )
    assert [row["code"] for row in queue.claim(now_epoch=T0 + 3, limit=1)] == ["000002"]
    assert [row["code"] for row in queue.claim(now_epoch=T0 + 4, limit=1)] == ["000003"]
    assert [row["code"] for row in queue.claim(now_epoch=T0 + 5, limit=1)] == ["000001"]
    assert queue.claim(now_epoch=T0 + 6, limit=1) == []  # prior claim is in flight


def test_restored_fund_does_not_reclaim_a_probe_and_preserves_ledger():
    queue = DiscoveryQueue(DAY)
    for code, name in [
        ("485810", "TIME 글로벌바이오액티브"),
        ("123450", "SOMETIME TECH"),
    ]:
        queue.observe(
            code=code,
            name=name,
            route="krx_nxt_integrated",
            observed_epoch=T0,
            received_epoch=T0 + 1,
            source_sha256=HASH_A,
            source_scope="observed_panel",
        )
    queue = DiscoveryQueue.restore(queue.snapshot(), session_date=DAY)
    claims = queue.claim(now_epoch=T0 + 2, limit=2)
    assert [row["code"] for row in claims] == ["123450"]
    fund = queue._candidates[("485810", "krx_nxt_integrated")]
    assert fund.source_sha256 == HASH_A and fund.claim_count == 0 and not fund.in_flight
    assert queue.claim_eligibility["product_ineligible_count"] == 1


def test_active_target_deferral_does_not_consume_claim_or_rotation_and_releases_immediately():
    queue = DiscoveryQueue(DAY)
    _observe(queue, "000001", kind="activity")
    _observe(queue, "000002", kind="gainers")
    claims = queue.claim(now_epoch=T0 + 2, limit=1, deferred_active_codes={"000001"})
    assert [r["code"] for r in claims] == ["000002"]
    active = queue._candidates[("000001", "krx_only")]
    assert (
        active.claim_count == 0
        and not active.in_flight
        and active.last_result == "queued"
    )
    assert queue.claim_eligibility["active_target_deferred_count"] == 1
    released = queue.claim(now_epoch=T0 + 3, limit=1, deferred_active_codes=set())
    assert released[0]["code"] == "000001"
    assert queue.claim_eligibility["eligible_due_wait_max_seconds"] == 0


def test_current_eligible_wait_is_observed_and_does_not_restore_historical_first_seen():
    queue = DiscoveryQueue(DAY)
    _observe(queue, "000001")
    queue.claim(now_epoch=T0 + 100, limit=0)
    assert queue.claim_eligibility["eligible_due_wait_max_seconds"] == 0
    queue.claim(now_epoch=T0 + 110, limit=0)
    assert queue.claim_eligibility["eligible_due_wait_max_seconds"] == 10
    restored = DiscoveryQueue.restore(queue.snapshot(), session_date=DAY)
    restored.claim(now_epoch=T0 + 111, limit=0)
    assert restored.claim_eligibility["eligible_due_wait_max_seconds"] == 0
    queue.claim(now_epoch=T0 + 112, limit=0, deferred_active_codes={"000001"})
    queue.claim(now_epoch=T0 + 113, limit=0)
    assert queue.claim_eligibility["eligible_due_wait_max_seconds"] == 0


def test_mixed_branches_keep_short_admission_and_rotate_four_long_slots():
    queue = DiscoveryQueue(DAY)
    for i in range(1, 6):
        _observe(queue, f"{i:06d}")
    requirement = lambda *args: dict(
        minimum_seconds=0, full_input_requirement_seconds=120
    )
    seen = set()
    for round in range(3):
        now = T0 + 2 + round * 160
        claims = queue.claim(now_epoch=now, limit=5, residence_requirements=requirement)
        assert len(claims) == 5
        long = [r for r in claims if r["residence_deadline_epoch"] - now == 150]
        assert len(long) == 4
        seen.update(r["code"] for r in long)
        for claim in claims:
            assert queue.resolve(
                claim,
                result="assessed",
                machine_action="RECHECK",
                next_due_epoch=now + 150,
                handoff_id=claim["physical_probe_lease_id"],
            )
            assert queue.close_handoff(claim, claim["physical_probe_lease_id"])
    assert len(seen) == 5


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
        ("KOSPI", "krx_only"),
        ("KOSDAQ", "krx_only"),
        ("KOSPI", "nxt_only"),
        ("KOSDAQ", "nxt_only"),
    )
    code = 1
    for market, route in cohorts:
        for _ in range(20):
            _observe(queue, f"{code:06d}", market=market, route=route)
            code += 1
    first = queue.claim(now_epoch=T0 + 2, limit=8)
    assert len(first) == 8
    assert {
        cohort: sum((row["market"], row["route"]) == cohort for row in first)
        for cohort in cohorts
    } == {cohort: 2 for cohort in cohorts}
    next_four = [
        queue.claim(now_epoch=T0 + 3 + index, limit=1)[0] for index in range(4)
    ]
    assert {(row["market"], row["route"]) for row in next_four} == set(cohorts)


def test_active_volume_candidates_get_bounded_priority_without_starving_gainers():
    queue = DiscoveryQueue(DAY)
    for index in range(1, 13):
        _observe(
            queue,
            f"{index:06d}",
            market="KOSPI" if index % 2 else "KOSDAQ",
            route="krx_nxt_integrated",
            kind="activity",
        )
    for index in range(13, 25):
        _observe(
            queue,
            f"{index:06d}",
            market="KOSPI" if index % 2 else "KOSDAQ",
            route="krx_nxt_integrated",
            kind="gainers",
        )

    first = queue.claim(now_epoch=T0 + 2, limit=8)
    assert [row["source_kind"] for row in first] == [
        "activity",
        "activity",
        "activity",
        "gainers",
        "activity",
        "activity",
        "activity",
        "gainers",
    ]
    assert {row["market"] for row in first if row["source_kind"] == "activity"} == {
        "KOSPI",
        "KOSDAQ",
    }
    assert {row["market"] for row in first if row["source_kind"] == "gainers"} == {
        "KOSPI",
        "KOSDAQ",
    }
    restored = DiscoveryQueue.restore(queue.snapshot(), session_date=DAY)
    assert {row["source_kind"] for row in restored.snapshot()["candidates"]} == {
        "activity",
        "gainers",
    }


def test_aftermarket_source_rotation_keeps_a_gainer_claim():
    queue = DiscoveryQueue(DAY)
    for index in range(1, 25):
        _observe(queue, f"{index:06d}", route="krx_nxt_integrated", kind="activity")
    for index in range(25, 33):
        _observe(queue, f"{index:06d}", route="krx_nxt_integrated", kind="gainers")
    first = queue.claim(
        now_epoch=T0 + 2,
        limit=8,
        activity_claims_per_gainer=7,
    )
    assert [row["source_kind"] for row in first] == ["activity"] * 7 + ["gainers"]
    second = DiscoveryQueue.restore(queue.snapshot(), session_date=DAY).claim(
        now_epoch=T0 + 10,
        limit=8,
        activity_claims_per_gainer=7,
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
    first = [
        queue.claim(now_epoch=T0 + 2 + index, limit=1)[0]["source_kind"]
        for index in range(4)
    ]
    assert first == ["activity", "activity", "activity", "gainers"]
    restored = DiscoveryQueue.restore(queue.snapshot(), session_date=DAY)
    second = [
        restored.claim(now_epoch=T0 + 10 + index, limit=1)[0]["source_kind"]
        for index in range(4)
    ]
    assert second == first


def test_exact_source_generation_and_route_block_stale_resolution():
    queue = DiscoveryQueue(DAY)
    assert _observe(queue, "000001") == "queued"
    claim = queue.claim(now_epoch=T0 + 2, limit=1)[0]
    assert _observe(queue, "000001", epoch=T0 + 3, digest=HASH_B) == "updated"
    assert queue.claim(now_epoch=T0 + 4, limit=1) == []
    assert queue.resolve(
        claim, result="assessed", machine_action="ENTER_NOW", next_due_epoch=T0 + 30
    )
    assert not queue.resolve(
        claim, result="assessed", machine_action="ENTER_NOW", next_due_epoch=T0 + 30
    )
    assert queue.claim(now_epoch=T0 + 5, limit=1)[0]["source_sha256"] == HASH_B
    assert _observe(queue, "000001", route="nxt_only") == "queued"
    assert (
        _observe(queue, "000001", epoch=T0 + 3, digest=HASH_A)
        == "source_generation_conflict"
    )
    assert len(queue.snapshot()["candidates"]) == 2


def test_source_gap_is_not_machine_block_and_restart_reclaims_inflight():
    queue = DiscoveryQueue(DAY)
    _observe(queue, "000001")
    claim = queue.claim(now_epoch=T0 + 2, limit=1)[0]
    with pytest.raises(ValueError):
        queue.resolve(
            claim,
            result="source_unavailable",
            machine_action="BLOCK",
            next_due_epoch=T0 + 30,
        )
    assert queue.resolve(claim, result="source_unavailable", next_due_epoch=T0 + 30)
    assert queue.snapshot()["candidates"][0]["machine_action"] == ""
    assert queue.claim(now_epoch=T0 + 29, limit=1) == []
    second = queue.claim(now_epoch=T0 + 30, limit=1)[0]
    restored = DiscoveryQueue.restore(queue.snapshot(), session_date=DAY)
    retry = restored.claim(now_epoch=T0 + 31, limit=1)[0]
    assert retry["code"] == second["code"]
    assert retry["claim_count"] == second["claim_count"] + 1
    assert not restored.resolve(
        second, result="assessed", machine_action="ENTER_NOW", next_due_epoch=T0 + 40
    )
    with pytest.raises(ValueError):
        DiscoveryQueue.restore(queue.snapshot(), session_date="2026-09-29")


@pytest.mark.parametrize(
    "result",
    [
        "source_unavailable",
        "required_feature_insufficient",
        "policy_unavailable",
        "active_conflict",
        "probe_capacity_deferred",
        "pattern_not_matched",
        "observation_incomplete",
    ],
)
def test_new_discovery_does_not_cancel_non_assessed_retry(result):
    queue = DiscoveryQueue(DAY)
    _observe(queue, "000001")
    claim = queue.claim(now_epoch=T0 + 2, limit=1)[0]
    assert queue.in_flight_count() == 1
    assert _observe(queue, "000001", epoch=T0 + 3, digest=HASH_B) == "updated"
    assert queue.resolve(claim, result=result, next_due_epoch=T0 + 64)
    assert queue.in_flight_count() == 0
    assert _observe(queue, "000001", epoch=T0 + 6, digest=HASH_A) == "updated"
    assert queue.claim(now_epoch=T0 + 63, limit=1) == []
    assert queue.claim(now_epoch=T0 + 64, limit=1)[0]["source_sha256"] == HASH_A


def test_refreshed_inflight_claim_timeout_still_rejects_late_result():
    queue = DiscoveryQueue(DAY)
    _observe(queue, "000001")
    claim = queue.claim(now_epoch=T0 + 2, limit=1)[0]
    assert _observe(queue, "000001", epoch=T0 + 3, digest=HASH_B) == "updated"
    restored = DiscoveryQueue.restore(queue.snapshot(), session_date=DAY)
    assert not restored.resolve(
        claim,
        result="assessed",
        machine_action="ENTER_NOW",
        next_due_epoch=T0 + 30,
    )
    refreshed = restored.claim(now_epoch=T0 + 7, limit=1)[0]
    assert refreshed["source_sha256"] == HASH_B
    assert (
        restored.abandon_expired_claims(
            now_epoch=refreshed["residence_deadline_epoch"], timeout_sec=60
        )
        == 1
    )
    assert not restored.resolve(
        refreshed,
        result="assessed",
        machine_action="ENTER_NOW",
        next_due_epoch=T0 + 80,
    )


def test_invalid_or_cross_day_source_cannot_enter_queue():
    queue = DiscoveryQueue(DAY)
    assert _observe(queue, "000001", route="unknown") == "route_unknown"
    assert _observe(queue, "000001", epoch=T0 - 86400) == "source_date_mismatch"
    assert (
        queue.observe(
            code="000001",
            route="krx_only",
            observed_epoch=T0,
            source_sha256=HASH_A,
            source_scope="whole_market",
            received_epoch=T0 + 1,
        )
        == "source_scope_unknown"
    )
    assert queue.snapshot()["candidates"] == []


def test_stale_observation_cannot_consume_probe_budget_until_refreshed():
    queue = DiscoveryQueue(DAY)
    assert _observe(queue, "000001") == "queued"
    assert (
        queue.claim(
            now_epoch=T0 + 121,
            limit=8,
            max_observation_age_sec=120,
        )
        == []
    )
    assert (
        queue.stale_candidate_count(now_epoch=T0 + 121, max_observation_age_sec=120)
        == 1
    )
    assert _observe(queue, "000001", epoch=T0 + 122, digest=HASH_B) == "updated"
    assert [
        row["code"]
        for row in queue.claim(
            now_epoch=T0 + 123,
            limit=8,
            max_observation_age_sec=120,
        )
    ] == ["000001"]


def test_four_long_leases_preserve_deadlines_capacity_and_cleanup_custody():
    queue = DiscoveryQueue(DAY)
    for i in range(6):
        _observe(queue, f"{i+1:06d}")
    required = lambda *args: {
        "minimum_seconds": 60,
        "full_input_requirement_seconds": 61,
    }
    claims = queue.claim(now_epoch=T0 + 2, limit=5, residence_requirements=required)
    assert len(claims) == 4
    assert all(c["residence_deadline_epoch"] == T0 + 152 for c in claims)
    assert queue.residence_deferred == {"long_slot_wait": 2}
    claim = claims[0]
    assert queue.resolve(
        claim,
        result="pattern_not_matched",
        next_due_epoch=T0 + 200,
        handoff_id=claim["physical_probe_lease_id"],
    )
    assert (
        queue.claim(now_epoch=T0 + 153, limit=2, residence_requirements=required) == []
    )
    assert queue.close_handoff(claim, claim["physical_probe_lease_id"])
    replacement = queue.claim(
        now_epoch=T0 + 154, limit=3, residence_requirements=required
    )
    assert len(replacement) == 1
    assert replacement[0]["code"] not in {c["code"] for c in claims}
    assert all(
        queue._candidates[(c["code"], c["route"])].residence_deadline_epoch == T0 + 152
        for c in claims[1:]
    )


def test_all_long_demand_borrows_idle_slot_without_sixth_lease_or_deadline_renewal():
    queue = DiscoveryQueue(DAY)
    for i in range(1, 8):
        _observe(queue, f"{i:06d}")
    required = lambda *args: dict(
        minimum_seconds=60, full_input_requirement_seconds=120
    )
    claims = queue.claim(
        now_epoch=T0 + 2,
        limit=50,
        residence_requirements=required,
        borrow_idle_short_slot=True,
    )
    assert len(claims) == queue.in_flight_count() == 5
    assert queue.claim_eligibility["idle_short_slot_borrowed"] is True
    assert all(c["residence_deadline_epoch"] == T0 + 152 for c in claims)
    c = claims[0]
    assert queue.resolve(
        c,
        result="observation_incomplete",
        next_due_epoch=T0 + 200,
        handoff_id=c["physical_probe_lease_id"],
    )
    queue.abandon_expired_claims(now_epoch=T0 + 153, timeout_sec=60)
    assert (
        queue.claim(
            now_epoch=T0 + 154,
            limit=5,
            residence_requirements=required,
            borrow_idle_short_slot=True,
        )
        == []
    )
    assert queue.close_handoff(c, c["physical_probe_lease_id"])
    replacements = queue.claim(
        now_epoch=T0 + 154,
        limit=5,
        residence_requirements=required,
        borrow_idle_short_slot=True,
    )
    assert (
        len(replacements) == 1
        and replacements[0]["physical_probe_lease_id"] != c["physical_probe_lease_id"]
    )
    assert all(
        queue._candidates[(r["code"], r["route"])].residence_deadline_epoch == T0 + 152
        for r in claims[1:]
    )


def test_short_demand_behind_long_backlog_keeps_its_reserved_slot():
    queue = DiscoveryQueue(DAY)
    for i in range(1, 9):
        _observe(queue, f"{i:06d}")
    required = lambda row, now: dict(
        minimum_seconds=0 if row.code == "000008" else 60,
        full_input_requirement_seconds=120,
    )
    claims = queue.claim(
        now_epoch=T0 + 2,
        limit=5,
        residence_requirements=required,
        borrow_idle_short_slot=True,
    )
    assert len(claims) == 5
    assert sum(c["residence_deadline_epoch"] == T0 + 152 for c in claims) == 4
    assert (
        next(c for c in claims if c["code"] == "000008")["residence_deadline_epoch"]
        == T0 + 62
    )


def test_fresh_activity_priority_keeps_one_oldest_service_turn():
    queue = DiscoveryQueue(DAY)
    _observe(queue, "000001", volume=1)
    for i in range(2, 7):
        _observe(queue, f"{i:06d}", volume=100 * i, epoch=T0 + 10)
    claims = queue.claim(now_epoch=T0 + 12, limit=4)
    assert [r["code"] for r in claims] == ["000006", "000005", "000004", "000001"]


def test_restored_products_are_rechecked_before_any_claim_is_consumed():
    queue = DiscoveryQueue(DAY)
    for code in ("487130", "005930", "123450"):
        _observe(queue, code)
    queue = DiscoveryQueue.restore(queue.snapshot(), session_date=DAY)
    claims = queue.claim(
        now_epoch=T0 + 2,
        limit=5,
        product_check=lambda code, name, market: dict(
            eligible=code == "005930",
            status="verified" if code == "005930" else "unverified",
        ),
    )
    assert [r["code"] for r in claims] == ["005930"]
    assert claims[0]["product_binding"]["eligible"] is True
    assert queue.claim_eligibility["product_ineligible_count"] == 2
    assert all(
        r.claim_count == 0 for r in queue._candidates.values() if r.code != "005930"
    )


def test_no_available_budget_does_not_evaluate_native_requirements():
    queue = DiscoveryQueue(DAY)
    _observe(queue, "000001")
    assert (
        queue.claim(
            now_epoch=T0 + 2,
            limit=0,
            borrow_idle_short_slot=True,
            residence_requirements=lambda *a: pytest.fail(
                "no capacity: native work must stay idle"
            ),
        )
        == []
    )


def test_age_turn_is_per_cohort_not_locked_to_every_fourth_gainer():
    queue = DiscoveryQueue(DAY)
    _observe(queue, "000001", volume=1, kind="activity")
    for i in range(2, 7):
        _observe(queue, f"{i:06d}", volume=100 * i, kind="activity", epoch=T0 + 10)
    _observe(queue, "000010", volume=100, kind="gainers")
    first = queue.claim(now_epoch=T0 + 12, limit=4)
    assert "000001" not in {r["code"] for r in first}
    for claim in first:
        assert queue.resolve(
            claim,
            result="pattern_not_matched",
            next_due_epoch=T0 + 100,
            handoff_id=claim["physical_probe_lease_id"],
        )
        assert queue.close_handoff(claim, claim["physical_probe_lease_id"])
    assert queue.claim(now_epoch=T0 + 13, limit=1)[0]["code"] == "000001"
