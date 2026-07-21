from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.engine.scalping import position_sizing_allocator as allocator

KST = ZoneInfo("Asia/Seoul")


def _context(
    at: str,
    source_signature="A,B,C",
    *,
    venue="KRX",
    budget=10_000_000,
    price=10_000,
    **overrides,
):
    values = {
        "allocation_stage": "initial_entry",
        "reference_time": datetime.fromisoformat(at).replace(tzinfo=KST),
        "source_signature": source_signature,
        "effective_venue": venue,
        "budget_base_krw": budget,
        "price_krw": price,
    }
    values.update(overrides)
    return allocator.ScalpingSizingContext(**values)


@pytest.mark.parametrize(
    ("at", "expected_tier"),
    [
        ("2026-07-21T09:29:59", 1),
        ("2026-07-21T09:30:00", 4),
        ("2026-07-21T11:29:59", 4),
        ("2026-07-21T11:30:00", 1),
        ("2026-07-21T13:29:59", 1),
        ("2026-07-21T13:30:00", 5),
        ("2026-07-21T15:19:59", 5),
        ("2026-07-21T15:20:00", 1),
    ],
)
def test_krx_time_boundaries(at, expected_tier):
    decision = allocator.resolve_scalping_allocation(_context(at))
    assert decision.tier == expected_tier


@pytest.mark.parametrize(
    ("source_signature", "expected_tier", "expected_ratio"),
    [
        ("-", 1, 0.10),
        ("A", 3, 0.20),
        ("A|B", 3, 0.20),
        (["A", "B", "C"], 4, 0.25),
        ("A,B,C,D", 4, 0.25),
        ("A,B,C,D,E", 2, 0.15),
        ("A,a,UNKNOWN,-", 3, 0.20),
    ],
)
def test_source_count_selects_five_stage_ratio(
    source_signature, expected_tier, expected_ratio
):
    decision = allocator.resolve_scalping_allocation(
        _context("2026-07-21T10:00:00", source_signature)
    )
    assert decision.tier == expected_tier
    assert decision.ratio == pytest.approx(expected_ratio)


def test_source_collection_elements_are_split_and_invalid_aliases_removed():
    decision = allocator.resolve_scalping_allocation(
        _context(
            "2026-07-21T10:00:00",
            ["A,B", "a|C", "N/A", "not applicable source signature"],
        )
    )
    assert decision.source_tokens == ("A", "B", "C")
    assert decision.source_count == 3
    assert decision.tier == 4


def test_afternoon_three_sources_selects_tier5_cap25():
    decision = allocator.resolve_scalping_allocation(
        _context("2026-07-21T14:00:00", "A,B,C")
    )
    assert decision.tier == 5
    assert decision.ratio == pytest.approx(0.25)


def test_nxt_and_unknown_venue_force_tier1():
    nxt = allocator.resolve_scalping_allocation(
        _context("2026-07-21T16:30:00", "A,B,C,D,E", venue="NXT")
    )
    unknown = allocator.resolve_scalping_allocation(
        allocator.ScalpingSizingContext(
            allocation_stage="initial_entry",
            reference_time=None,
            source_signature="A,B,C",
            effective_venue="UNKNOWN",
            budget_base_krw=10_000_000,
            price_krw=10_000,
        )
    )
    assert (nxt.tier, nxt.ratio, nxt.tier_reason) == (
        1,
        0.10,
        "nxt_forced_tier1",
    )
    assert unknown.tier == 1
    assert unknown.tier_reason == "unknown_venue_fallback"


@pytest.mark.parametrize("venue", [None, "", "UNKNOWN", "UNRESOLVED"])
def test_missing_or_unknown_venue_does_not_infer_krx_from_clock(venue):
    decision = allocator.resolve_scalping_allocation(
        _context("2026-07-21T10:00:00", "A,B,C", venue=venue)
    )

    assert decision.venue == "UNKNOWN"
    assert (decision.tier, decision.ratio) == (1, pytest.approx(0.10))
    assert decision.tier_reason == "unknown_venue_fallback"


def test_max_position_qty_cap_is_derived_from_budget_and_price():
    assert allocator.max_position_qty_cap_from_budget(10_000_000, 100_000, 0.20) == 20
    assert allocator.max_position_qty_cap_from_budget(10_000_000, 100_000, 2.0) == 100
    assert allocator.max_position_qty_cap_from_budget(10_000_000, 0, 0.20) == 0


def test_invalid_ratio_configuration_fails_closed(monkeypatch):
    monkeypatch.setattr(allocator, "TIER_RATIOS", (0.10, 0.30, 0.20, 0.25, 0.25))
    decision = allocator.resolve_scalping_allocation(
        _context("2026-07-21T14:00:00", "A,B,C")
    )
    assert decision.tier == 1
    assert decision.ratio == pytest.approx(0.10)
    assert decision.tier_reason == "invalid_sizing_config_fallback"
    assert decision.config_valid is False


def test_initial_tier_reuse_and_nxt_override():
    reused = allocator.resolve_scalping_allocation(
        _context(
            "2026-07-21T10:10:00",
            "-",
            allocation_stage="avg_down",
            initial_tier=5,
            initial_formula_version=allocator.FORMULA_VERSION,
        )
    )
    nxt = allocator.resolve_scalping_allocation(
        _context(
            "2026-07-21T16:30:00",
            "A,B,C",
            venue="NXT",
            allocation_stage="pyramid",
            initial_tier=5,
            initial_formula_version=allocator.FORMULA_VERSION,
        )
    )
    assert reused.tier == 5
    assert reused.tier_reason == "reused_initial_entry_tier"
    assert nxt.tier == 1


def test_budget_floor_and_all_quantity_caps_are_composed():
    decision = allocator.resolve_scalping_allocation(
        _context(
            "2026-07-21T10:00:00",
            "A,B,C",
            budget=1_000_000,
            price=100_000,
            cash_orderable_qty_cap=8,
            remaining_position_qty_cap=6,
            stage_qty_cap=4,
            broker_qty_cap=3,
        )
    )
    assert decision.target_budget == 250_000
    assert decision.safe_budget == 237_500
    assert decision.pre_cap_qty == 2
    assert decision.effective_qty == 2
    assert decision.binding_caps == ()

    capped = allocator.resolve_scalping_allocation(
        _context(
            "2026-07-21T10:00:00",
            "A,B,C",
            budget=10_000_000,
            price=100_000,
            cash_orderable_qty_cap=20,
            remaining_position_qty_cap=10,
            stage_qty_cap=5,
            broker_qty_cap=3,
        )
    )
    assert capped.pre_cap_qty == 23
    assert capped.effective_qty == 3
    assert capped.binding_caps == (
        "cash_orderable_qty_cap",
        "remaining_position_qty_cap",
        "stage_qty_cap",
        "broker_qty_cap",
    )


def test_min_one_share_floor_never_bypasses_cash_qty_cap():
    floor = allocator.resolve_scalping_allocation(
        _context(
            "2026-07-21T09:10:00",
            "A",
            budget=100_000,
            price=60_000,
        )
    )
    blocked = allocator.resolve_scalping_allocation(
        _context(
            "2026-07-21T09:10:00",
            "A",
            budget=100_000,
            price=60_000,
            cash_orderable_qty_cap=0,
        )
    )
    assert floor.pre_cap_qty == 1
    assert floor.min_one_share_floor_applied is True
    assert blocked.effective_qty == 0
    assert blocked.min_one_share_floor_applied is False
    assert blocked.binding_caps == ("cash_orderable_qty_cap",)


def test_min_one_share_floor_never_bypasses_absolute_budget_cap():
    decision = allocator.resolve_scalping_allocation(
        _context(
            "2026-07-21T09:10:00",
            "A",
            budget=1_000_000,
            price=600_000,
            absolute_budget_cap_krw=500_000,
        )
    )
    assert decision.target_budget == 100_000
    assert decision.pre_cap_qty == 0
    assert decision.effective_qty == 0
    assert decision.min_one_share_floor_applied is False
    assert decision.binding_caps == ("absolute_budget_cap",)


def test_current_position_is_composed_with_max_position_cap():
    decision = allocator.resolve_scalping_allocation(
        _context(
            "2026-07-21T10:00:00",
            "A,B,C",
            budget=10_000_000,
            price=100_000,
            current_position_qty=7,
            max_position_qty_cap=10,
        )
    )
    assert decision.pre_cap_qty == 23
    assert decision.effective_qty == 3
    assert decision.binding_caps == ("max_position_qty_cap",)


@pytest.mark.parametrize(
    "allocation_stage",
    ["initial_entry", "opening_rotation_initial", "rising_missed_scout_initial"],
)
def test_all_initial_entry_lineages_share_the_same_allocator(allocation_stage):
    decision = allocator.resolve_scalping_allocation(
        _context(
            "2026-07-21T14:00:00",
            "A,B,C",
            allocation_stage=allocation_stage,
        )
    )
    assert decision.formula_version == allocator.FORMULA_VERSION
    assert (decision.tier, decision.ratio, decision.effective_qty) == (5, 0.25, 237)
