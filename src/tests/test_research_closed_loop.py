from copy import deepcopy
from datetime import date, datetime
import json
import os

import pytest

from src.engine.monitoring import research_closed_loop as loop
from src.engine.monitoring import research_source_facts as facts

DAY = date(2026, 9, 17)


def candidate(**changes):
    return loop.candidate_revision(
        symbol="000001",
        parameters={"target_bps": 50},
        source_date=DAY,
        source_sha256="a" * 64,
        cost_sha256="b" * 64,
        frozen_at=datetime.fromisoformat("2026-09-17T20:10:00+09:00"),
        **changes,
    )


def test_candidate_is_frozen_and_calendar_cannot_slide(tmp_path):
    revision = candidate()
    assert loop.freeze_candidate(revision, directory=tmp_path) == revision
    changed = candidate(lane_id="different")
    assert changed["revision_sha256"] != revision["revision_sha256"]
    changed = deepcopy(revision)
    changed["parameters"]["target_bps"] = 100
    with pytest.raises(ValueError):
        loop.freeze_candidate(changed, directory=tmp_path)
    shifted = deepcopy(revision)
    shifted["holdout_dates"] = loop.trading_dates_after(
        date.fromisoformat(shifted["holdout_dates"][0]), 16
    )
    shifted["revision_sha256"] = loop.digest(
        {k: v for k, v in shifted.items() if k != "revision_sha256"}
    )
    with pytest.raises(ValueError, match="calendar"):
        loop.validate_revision(shifted)
    required = revision["calibration_dates"] + revision["holdout_dates"]
    window = loop.prospective_window(
        revision,
        source_date=date.fromisoformat(required[-1]),
        qualified_dates=required[1:],
    )
    assert window["status"] == "source_gap"
    assert window["missing_dates"] == required[:1]
    assert (
        loop.prospective_window(revision, source_date=DAY, qualified_dates=[])["status"]
        == "waiting"
    )


def test_late_historical_research_does_not_backdate_seed():
    late = candidate()
    late = loop.candidate_revision(
        symbol="000001",
        parameters={},
        source_date=DAY,
        source_sha256="a" * 64,
        cost_sha256="b" * 64,
        frozen_at=datetime.fromisoformat("2026-10-01T20:10:00+09:00"),
    )
    assert late["calibration_dates"][0] > "2026-10-01"
    loop.validate_revision(late)


@pytest.mark.parametrize("name", ["../000001", "/tmp/000001", "", "é"])
def test_candidate_path_cannot_escape_registry(tmp_path, name):
    with pytest.raises(ValueError):
        loop.load_candidate("000001", lane_id=name, directory=tmp_path)


def test_partial_multifile_publish_and_conflicting_retry_fail_closed(tmp_path):
    files = {"policy.json": {"policy": 1}, "catalog.json": {"seed": 1}}
    manifest = loop.publication_transaction(tmp_path, effective_date=DAY, files=files)
    assert (
        loop.publication_transaction(tmp_path, effective_date=DAY, files=files)
        == manifest
    )
    (tmp_path / "catalog.json").unlink()
    with pytest.raises((OSError, ValueError)):
        loop.verify_publication(
            tmp_path, effective_date=DAY, name="policy.json", value=files["policy.json"]
        )
    loop.atomic_write(tmp_path / "catalog.json", files["catalog.json"])
    assert (
        loop.verify_publication(
            tmp_path, effective_date=DAY, name="policy.json", value=files["policy.json"]
        )
        == manifest
    )
    with pytest.raises(ValueError, match="conflict"):
        loop.publication_transaction(
            tmp_path, effective_date=DAY, files={"policy.json": {"policy": 2}}
        )
    assert loop.read_object(tmp_path / "policy.json") == files["policy.json"]
    loop.atomic_write(
        tmp_path / ".generations" / manifest["generation_sha256"] / "policy.json",
        {"policy": 3},
    )
    with pytest.raises(ValueError):
        loop.verify_publication(
            tmp_path, effective_date=DAY, name="policy.json", value=files["policy.json"]
        )


def test_symlink_source_and_output_fail_closed(tmp_path):
    loop.atomic_write(tmp_path / "real.json", {"test": 1})
    (tmp_path / "link.json").symlink_to(tmp_path / "real.json")
    with pytest.raises(ValueError):
        loop.read_object(tmp_path / "link.json")
    with pytest.raises(ValueError):
        loop.atomic_write(tmp_path / "link.json", {"test": 2})


def test_actual_consumer_receipt_contains_current_process(tmp_path):
    path = loop.consumer_receipt(
        owner="widget",
        effective_date=DAY,
        accepted={"000001": {"policy_hash": "a" * 64}},
        directory=tmp_path,
    )
    receipt = loop.read_object(path)
    assert receipt["pid"] == os.getpid()
    assert receipt["cwd"] == os.getcwd()
    assert receipt["accepted_policy_sha256"] == loop.digest(receipt["accepted"])
    assert receipt["actual_order_submitted"] is False


def allocator():
    body = dict(
        schema="machine_research_allocator_snapshot_v1",
        source_date=DAY.isoformat(),
        available_cash_krw=2001,
        exposure_limit_krw=2001,
        holding_notional_krw=0,
        reserved_notional_krw=0,
        source_quality_status="PASS",
        owner_conflict=False,
        owner_contract_sha256="c" * 64,
        allocator_rule="fixed_existing_allocator_no_research_arbitration",
        exposure_limit_basis="native_existing_allocator_contract",
        **loop.AUTHORITY,
    )
    constraints = dict(
        source_date=str(DAY),
        owner_contract_sha256="c" * 64,
        same_stage_clear=True,
        buy_fee_bps=1.5,
        cooldown_contract_status="verified_native_family_policy",
        venue_session_contract="KRX/KRX_REGULAR",
        per_leg_quantity=10,
        **loop.AUTHORITY,
    )
    body["constraints"] = {**constraints, "contract_sha256": loop.digest(constraints)}
    return {**body, "snapshot_sha256": loop.digest(body)}


def test_joint_gate_never_prunes_infeasible_winners_or_invents_unknown_profit():
    episode = dict(
        entry_at="2026-09-17T09:10:00+09:00",
        exit_at="2026-09-17T09:11:00+09:00",
        entry_price=100,
        net_return_pct=1,
    )
    rows = {"000001": [episode], "000002": [episode]}
    assert (
        loop.joint_allocation(
            rows, snapshot=None, source_date=DAY, parent_sha256="a" * 64
        )["feasible_combined_net_profit_krw"]
        is None
    )
    assert (
        loop.joint_allocation(
            rows, snapshot=allocator(), source_date=DAY, parent_sha256="a" * 64
        )["status"]
        == "pass"
    )
    snapshot = allocator()
    snapshot["reserved_notional_krw"] = 1
    snapshot["snapshot_sha256"] = loop.digest(
        {k: v for k, v in snapshot.items() if k != "snapshot_sha256"}
    )
    blocked = loop.joint_allocation(
        rows, snapshot=snapshot, source_date=DAY, parent_sha256="a" * 64
    )
    assert blocked["status"] == "allocation_blocked"
    assert blocked["feasible_combined_net_profit_krw"] is None
    assert blocked["demand"]["independent_modeled_net_profit_krw"] == 20


def test_shared_facts_decode_once_per_generation_and_are_immutable(tmp_path):
    path = tmp_path / "raw.jsonl"
    row = dict(
        symbol="000001",
        bbo={"best_bid": 100},
        observation_seed={"parameters_sha256": "a"},
    )
    path.write_text(json.dumps(row) + "\n")
    before = facts.COUNTERS["full_decodes"]
    sha, first = facts.completed_day_facts(path)
    for _ in range(4):
        assert facts.completed_day_facts(path) == (sha, first)
    assert facts.COUNTERS["full_decodes"] == before + 1
    with pytest.raises(TypeError):
        first[0]["bbo"]["best_bid"] = 999
    row["bbo"]["best_bid"] = 200
    path.write_text(json.dumps(row) + "\n")
    assert facts.completed_day_facts(path)[0] != sha
    assert facts.COUNTERS["full_decodes"] == before + 2


def test_admission_uses_native_source_not_forward_label(tmp_path):
    receipt = dict(
        contract_valid=True,
        causal_rows=[
            {
                "stock_code": "000001",
                "venue": "KRX",
                "symbol_master_status": "verified",
                "instrument_type": "EQUITY",
                "listing_market": "KOSPI",
                "market_data_route": "krx_only",
            }
        ],
        emitted_at="2026-09-17T10:00:00+09:00",
        source_cycle_id="native-cycle",
        rows_sha256="a" * 64,
        declared_counts={"omitted": 0},
    )
    census = dict(
        target_date=DAY.isoformat(),
        scanner_source_census={"receipts": [receipt, receipt]},
        opportunity_details={
            "forward_winner": {"stock_code": "000002", "profit": 9999}
        },
    )
    catalog = loop.admission_catalog(census)
    assert catalog["native_count"] == 1
    loop.write_admissions(census, directory=tmp_path)
    assert loop.admission_symbols(DAY, owner="widget", directory=tmp_path) == {
        "000001": "000001"
    }
    assert (
        loop.admission_symbols(date(2026, 9, 16), owner="widget", directory=tmp_path)
        == {}
    )


@pytest.mark.parametrize("seed_count", [1, 4])
def test_shared_ws_writer_tags_only_already_frozen_seeds_without_remote_calls(
    tmp_path, seed_count
):
    from src.tests.test_dynamic_micro_confirmation import _live_snapshot
    from datetime import timedelta

    revision = loop.candidate_revision(
        symbol="005930",
        parameters={},
        source_date=DAY,
        source_sha256="a" * 64,
        cost_sha256="b" * 64,
        frozen_at=datetime.fromisoformat("2026-09-17T20:10:00+09:00"),
    )
    loop.freeze_candidate(revision, directory=tmp_path)
    for index in range(1, seed_count):
        value = loop.candidate_revision(
            symbol="005930",
            parameters={"target_bps": 50 + index},
            source_date=DAY,
            source_sha256="a" * 64,
            cost_sha256="b" * 64,
            lane_id=f"seed_{index}",
            frozen_at=datetime.fromisoformat(revision["frozen_at"]),
        )
        loop.freeze_candidate(value, directory=tmp_path)
    now = datetime.fromisoformat(revision["calibration_dates"][0] + "T09:05:00+09:00")
    source = tmp_path / "ws.json"
    loop.atomic_write(source, _live_snapshot(now, item="005930"))
    writer = facts.SharedResearchFactWriter(
        ["005930", "000002"], directory=tmp_path, snapshot_path=source
    )
    receipt = writer.collect_once(now)
    assert receipt["remote_requests"] == 0 and receipt["written_facts"] == 2
    assert writer.collect_once(now)["written_facts"] == 0
    path = tmp_path / "facts" / f"prospective_facts_005930_{now:%Y%m%d}.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert all(
        len(row["seed_memberships"]) == seed_count
        and any(
            member["revision_sha256"] == revision["revision_sha256"]
            for member in row["seed_memberships"]
        )
        for row in rows
    )
    invalid = _live_snapshot(now + timedelta(seconds=1), item="005930_NX")
    loop.atomic_write(source, invalid)
    assert writer.collect_once(now + timedelta(seconds=1))["written_facts"] == 0


def test_optional_cache_cap_never_deletes_required_evidence(tmp_path):
    root = tmp_path / "cache"
    root.mkdir()
    required = tmp_path / "raw.jsonl"
    required.write_text("required\n")
    path = root / "000001" / "day.json.z"
    assert loop.optional_cache_write(
        path, b"1234", cache_root=root, soft_cap=4, reserve=0
    )
    assert not loop.optional_cache_write(
        root / "000002" / "day.json.z", b"5", cache_root=root, soft_cap=4, reserve=0
    )
    assert path.read_bytes() == b"1234" and required.read_text() == "required\n"
    assert not loop.optional_cache_write(
        path, b"12345", cache_root=root, soft_cap=4, reserve=0
    )


def market_days(count=3):
    from src.engine.monitoring.widget_symbol_signal_policy_research import Bar, KST
    from datetime import timedelta
    import math

    days = [
        date.fromisoformat(value)
        for value in loop.trading_dates_after(date(2026, 8, 1), count)
    ]
    result = {}
    for number, day in enumerate(days):
        start = datetime.combine(day, time_minute(9, 0), tzinfo=KST)
        rows = []
        for minute in range(390):
            close = 10000 + round(150 * math.sin(minute / 6)) + number * 3
            rows.append(
                Bar(
                    start + timedelta(minutes=minute),
                    close - 3,
                    close + 9,
                    close - 9,
                    close,
                    600 if minute % 7 == 6 else 100,
                )
            )
        result[day] = tuple(rows)
    return result


def time_minute(hour, minute):
    from datetime import time

    return time(hour, minute)


def test_full_grid_setup_jump_matches_reference_and_warm_append_replays_only_new_day(
    tmp_path,
):
    from src.engine.monitoring import widget_symbol_signal_policy_research as research

    grouped = market_days()
    days = list(grouped)
    cold = research.ReplayContext(
        {day: grouped[day] for day in days[:2]}, tmp_path / "cache" / "000001"
    )
    episode_count = 0
    for policy in research.policy_grid():
        actual = research.evaluate_policy(
            cold.grouped, days[:2], policy, include_episodes=True, replay_context=cold
        )
        reference = research.evaluate_policy(
            cold.grouped, days[:2], policy, include_episodes=True
        )
        assert actual == reference
        episode_count += len(actual["episodes"])
    assert episode_count > 0
    cold.flush()
    warm = research.ReplayContext(grouped, tmp_path / "cache" / "000001")
    for policy in research.policy_grid():
        research.evaluate_policy(
            grouped, days, policy, include_episodes=True, replay_context=warm
        )
    assert warm.cache_hits == 2 * 1536
    assert warm.cache_misses == 1536
    warm.flush()
    assert warm.cache_write_skips == 0


def test_native_capacity_source_is_once_per_account_and_never_uses_operator_floor(
    tmp_path, monkeypatch,
):
    from src.engine.monitoring.research_native_capacity_source import acquire

    from types import SimpleNamespace
    from src.engine.monitoring import research_native_capacity_source as source

    captured = datetime.fromisoformat(str(DAY) + "T20:05:00+09:00")
    monkeypatch.setattr(source, "datetime", SimpleNamespace(
        now=lambda tz: captured,
        fromisoformat=datetime.fromisoformat,
    ))
    calls = []

    def inventory(token):
        calls.append("inventory")
        return [], {"KRX", "NXT"}, {"normalization_contract_complete": True}

    def unfilled(token):
        calls.append("unfilled")
        return [], {"normalization_contract_complete": True, "request_succeeded": True}

    def deposit(token):
        calls.append("deposit")
        return 99999999

    def capacity(token, symbol, **kwargs):
        calls.append("capacity")
        assert symbol == "005930" and kwargs["is_nxt"] is False
        return dict(
            cash_only_orderable_amount=200000,
            cash_only_orderable_qty=10,
            cash_orderable_contract_status="valid",
            capacity_source_sha256="a" * 64,
            capacity_contract_version=1,
            requested_stock_code=symbol,
            error="",
            capacity_observed_at=captured.isoformat(),
        )

    adapters = dict(
        inventory=inventory,
        unfilled=unfilled,
        deposit=deposit,
        deposit_meta=lambda: dict(
            source="api_fresh", raw_amount=100000, minimum_floor_applied=True
        ),
        capacity=capacity,
    )
    result = acquire(DAY, directory=tmp_path, token="fixture", adapters=adapters)
    assert result["status"] == "complete" and calls == [
        "inventory",
        "unfilled",
        "deposit",
        "capacity",
    ]
    assert (
        loop.read_object(tmp_path / "native_capacity" / str(DAY) / "native_cash.json")[
            "cash_context"
        ]["account_deposit"]
        == 100000
    )
    assert (
        result["order_requests"] == 0
        and result["research_count_dependent_requests"] == 0
    )
    adapters["deposit_meta"] = lambda: dict(
        source="virtual_override", raw_amount=100000
    )
    assert (
        acquire(DAY, directory=tmp_path, token="fixture", adapters=adapters)["status"]
        == "source_gap"
    )


def test_joint_allocator_missing_fee_cannot_be_zero_cost(tmp_path):
    snapshot = allocator()
    snapshot["constraints"].pop("buy_fee_bps")
    snapshot["constraints"]["contract_sha256"] = loop.digest(
        {k: v for k, v in snapshot["constraints"].items() if k != "contract_sha256"}
    )
    snapshot["snapshot_sha256"] = loop.digest(
        {k: v for k, v in snapshot.items() if k != "snapshot_sha256"}
    )
    assert (
        loop.joint_allocation(
            {}, snapshot=snapshot, source_date=DAY, parent_sha256="x"
        )["status"]
        == "allocation_blocked"
    )


def test_book_conflict_invalidates_cached_reader_without_scanning_raw(tmp_path):
    path = tmp_path / "prospective_facts_000001_20260917.jsonl"
    path.write_text(json.dumps({"observed_at_kst": "2026-09-17T09:03:00+09:00"}) + "\n")
    facts.indexed_day_facts(path, windows=[])
    path.with_name("source_gap_000001_20260917.json").write_text("{}")
    with pytest.raises(ValueError, match="identity_conflict"):
        facts.indexed_day_facts(path, windows=[])


def test_closed_loop_retirement_requires_exact_mature_version_and_preserves_custody():
    from src.engine.automation.low_price_two_leg_auto_expansion_policy import (
        _mature_nonperforming_profile_ids,
    )

    report = dict(closed_loop_contract=loop.SCHEMA, trading_date_count=120, profiles={})
    assert _mature_nonperforming_profile_ids(report) == set()
    full = dict(
        exact_completed_count=6,
        exact_completed_legs=8,
        realized_net_return_pct=-0.1,
        profile_ids=["auto_000001_midday", "manual_000001"],
    )
    tail = dict(
        exact_completed_count=3, exact_completed_legs=4, realized_net_return_pct=-0.1
    )
    report["policy_version_feedback"] = dict(
        cumulative=dict(strategy_revisions={"a" * 64: full}),
        holdout_last_16=dict(strategy_revisions={"a" * 64: tail}),
    )
    assert _mature_nonperforming_profile_ids(report) == {"auto_000001_midday"}
    tail["realized_net_return_pct"] = None
    assert _mature_nonperforming_profile_ids(report) == set()


def test_late_publication_receipt_retains_served_version_and_marks_unconsumed(tmp_path):
    path = loop.consumer_receipt(
        owner="episode",
        effective_date=DAY,
        accepted={"old": {"policy_content_sha256": "a" * 64}},
        rejected={"new": "published_not_consumed"},
        directory=tmp_path,
    )
    receipt = loop.read_object(path)
    assert receipt["status"] == "published_not_consumed"
    assert receipt["accepted"]["old"]["policy_content_sha256"] == "a" * 64
    assert receipt["rejected"] == {"new": "published_not_consumed"}
    assert receipt["actual_order_submitted"] is False


def test_completed_study_fixed_point_publishes_valid_empty_and_blocks_changed_dependency(
    tmp_path, monkeypatch
):
    from src.engine.automation import machine_research_closed_loop_refresh as phase
    from src.tests.test_widget_symbol_runtime_policy import _research
    from src.engine.monitoring import widget_symbol_signal_policy_research as widget
    from src.engine.monitoring import (
        low_price_two_leg_expanded_candidate_research as episode,
    )

    monkeypatch.setattr(phase, "DATA_DIR", tmp_path / "data")
    root = tmp_path / "report"
    directory = tmp_path / "runtime" / "machine_research_closed_loop"
    report = _research()
    report.update(end_date=str(DAY), closed_loop_contract=loop.SCHEMA)
    for result in report["symbols"].values():
        result.pop("selected_policy", None)
        result.update(name="fixture", decision="hold_sample_insufficient_signal")
    peer = dict(
        schema=episode.REPORT_SCHEMA,
        target_date=str(DAY),
        end_date=str(DAY),
        start_date="2026-06-05",
        status="no_qualified_candidate",
        profiles={},
        recommendations=[],
        postclose_logic_recommendations=[],
        recommendation_count=0,
        trading_date_count=72,
        calibration_trading_day_count=56,
        holdout_trading_day_count=16,
        closed_loop_contract=loop.SCHEMA,
        **loop.AUTHORITY,
    )
    with loop.research_scope(directory):
        widget.write_report(
            report, output_dir=root / "widget_symbol_signal_policy_research"
        )
        episode.write_report(
            peer, output_dir=root / "low_price_two_leg_expanded_candidate_research"
        )
    first = phase.refresh(DAY, directory=directory, report_root=root)
    assert first["status"] == "complete" and phase.validate_current_receipt(first, DAY)
    assert first["publications"]["widget"]["profile_count"] == 0
    from src.engine.monitoring import research_version_outcomes as outcomes

    monkeypatch.setattr(
        outcomes,
        "collect_widget_outcomes",
        lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("completed retry must not query costs")
        ),
    )
    second = phase.refresh(DAY, directory=directory, report_root=root)
    assert second == first
    source = (
        root
        / "widget_symbol_signal_policy_research"
        / f"widget_symbol_signal_policy_research_{DAY}.json"
    )
    corrected = loop.read_object(source)
    corrected["source_correction"] = True
    loop.atomic_write(source, corrected)
    assert not phase.validate_current_receipt(first, DAY)


def test_sealed_fact_archive_preserves_original_bytes_and_point_read_boundaries(
    tmp_path,
):
    from datetime import timedelta
    from src.engine.monitoring.research_fact_archive import seal_fact_file

    path = tmp_path / "prospective_facts_000001_20260917.jsonl"
    start = datetime.fromisoformat("2026-09-17T09:03:00+09:00")
    rows = [
        dict(
            observed_at_kst=(start + timedelta(seconds=i)).isoformat(),
            native=i,
            repeated="x" * 1000,
        )
        for i in range(600)
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    sha, selected = facts.indexed_day_facts(
        path, windows=[(start + timedelta(seconds=254), start + timedelta(seconds=259))]
    )
    before_bytes = path.stat().st_size
    archived = seal_fact_file(path, expected_sha256=sha)
    assert not path.exists() and archived.stat().st_size < before_bytes / 5
    archived_sha, point = facts.indexed_day_facts(
        archived,
        windows=[(start + timedelta(seconds=254), start + timedelta(seconds=259))],
    )
    assert archived_sha == sha and point == selected
    assert [row["native"] for row in point] == list(range(254, 260))
    raw = archived.read_bytes()
    archived.write_bytes(raw[:-1])
    with pytest.raises(ValueError, match="footer"):
        facts.indexed_day_facts(archived, windows=[])


def test_interrupted_archive_never_discards_original_required_evidence(tmp_path):
    from src.engine.monitoring.research_fact_archive import seal_fact_file

    path = tmp_path / "prospective_facts_000001_20260917.jsonl"
    path.write_bytes(b'{"incomplete":')
    with pytest.raises(ValueError, match="incomplete"):
        seal_fact_file(path)
    assert path.read_bytes() == b'{"incomplete":'
    assert not path.with_suffix(".jsonl.zfb").exists()


def test_joint_cohorts_accept_later_causal_admission_without_moving_earlier_window(
    tmp_path, monkeypatch
):
    import src.engine.monitoring.research_closed_loop as module

    clock = [datetime.fromisoformat("2026-09-17T20:10:00+09:00")]

    class NativeClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return clock[0].astimezone(tz) if tz else clock[0]

    monkeypatch.setattr(module, "datetime", NativeClock)
    first = candidate()
    loop.freeze_candidate(first, directory=tmp_path)
    inputs = [dict(candidate_revisions={"first": first})]
    original = loop.freeze_joint_bundle(inputs, directory=tmp_path)
    assert original
    clock[0] = datetime.fromisoformat(first["holdout_dates"][0] + "T20:10:00+09:00")
    later = loop.candidate_revision(
        symbol="000002",
        parameters={},
        source_date=clock[0].date(),
        frozen_at=clock[0],
        source_sha256="c" * 64,
        cost_sha256="b" * 64,
    )
    loop.freeze_candidate(later, directory=tmp_path)
    changed = loop.freeze_joint_bundle(
        [dict(candidate_revisions={"first": first, "later": later})], directory=tmp_path
    )
    assert len(changed["cohort_manifests"]) == 2
    assert (
        next(iter(original["cohort_manifests"].values()))
        in changed["cohort_manifests"].values()
    )
    assert (
        first["holdout_dates"]
        == inputs[0]["candidate_revisions"]["first"]["holdout_dates"]
    )


def test_joint_cohort_cannot_drop_an_unreplaced_member_after_holdout(
    tmp_path, monkeypatch
):
    clock = datetime.fromisoformat("2026-09-17T20:10:00+09:00")

    class NativeClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return clock

    monkeypatch.setattr(loop, "datetime", NativeClock)
    a = candidate()
    b = loop.candidate_revision(
        symbol="000002",
        parameters={},
        source_date=DAY,
        frozen_at=clock,
        source_sha256="c" * 64,
        cost_sha256="b" * 64,
    )
    for revision in (a, b):
        loop.freeze_candidate(revision, directory=tmp_path)
    loop.freeze_joint_bundle(
        [dict(candidate_revisions={"a": a, "b": b})], directory=tmp_path
    )
    with pytest.raises(ValueError, match="pruned"):
        loop.frozen_joint_bundle(
            [dict(candidate_revisions={"a": a})], directory=tmp_path
        )


def test_new_unfilled_symbol_bootstraps_cf_validation_and_next_date_publication(
    tmp_path, monkeypatch
):
    """Advance an isolated source-only fixture through the prospective calendar."""
    from datetime import timedelta
    from src.engine.automation import machine_research_closed_loop_refresh as phase
    from src.engine.monitoring import research_allocation_snapshot as funding
    from src.engine.monitoring import policy_research_economics as economics
    from src.engine.monitoring import widget_symbol_runtime_policy as publisher
    from src.engine.monitoring import widget_symbol_signal_policy_research as widget
    from src.engine.monitoring import (
        low_price_two_leg_expanded_candidate_research as episode,
    )
    from src.engine.monitoring.widget_execution_quality import load_execution_incidents
    from src.engine.monitoring.widget_comparison_cost import comparison_cost_contract
    from src.trading.config.symbol_owner_policy import build_symbol_owner_policy_payload
    from src.tests.test_widget_symbol_runtime_policy import _research

    code = "000009"
    clock = [datetime.fromisoformat("2026-09-17T20:10:00+09:00")]

    class NativeClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return clock[0].astimezone(tz) if tz else clock[0]

    monkeypatch.setattr(loop, "datetime", NativeClock)
    monkeypatch.setattr(economics, "datetime", NativeClock)
    monkeypatch.setattr(phase, "DATA_DIR", tmp_path / "data")
    directory, root = (
        tmp_path / "runtime" / "machine_research_closed_loop",
        tmp_path / "report",
    )
    report = _research()
    parameters = report["symbols"]["006800"]["selected_policy"]
    revision = loop.candidate_revision(
        symbol=code,
        parameters=parameters,
        source_date=DAY,
        frozen_at=clock[0],
        source_sha256="a" * 64,
        cost_sha256=comparison_cost_contract(DAY)["contract_sha256"],
    )
    loop.freeze_candidate(revision, directory=directory)
    loop.freeze_joint_bundle(
        [dict(candidate_revisions={code: revision})], directory=directory
    )
    cal, hold = revision["calibration_dates"], revision["holdout_dates"]
    completed_day = date.fromisoformat(hold[-1])
    clock[0] = datetime.fromisoformat(str(completed_day) + "T20:10:00+09:00")
    selected_rows = []
    for native_day in cal + hold[:4]:
        signal = datetime.fromisoformat(native_day + "T12:00:00+09:00")
        entry, exit_ = signal + timedelta(minutes=1), signal + timedelta(minutes=2)
        cost = comparison_cost_contract(signal.date())
        row = dict(
            trade_date=native_day,
            signal_at=signal.isoformat(),
            entry_at=entry.isoformat(),
            exit_at=exit_.isoformat(),
            entry_price=10000,
            exit_price=10050,
            target_price=10050,
            exit_reason="target",
            entry_state="ENTRY_READY",
            peak_return_pct=0.5,
            net_return_pct=round(0.5 - cost["round_trip_cost_pct"], 6),
            daily_entry_ordinal=1,
            cost_contract_sha256=cost["contract_sha256"],
        )
        selected_rows.append(row)
        facts_path = (
            directory / "facts" / f"prospective_facts_{code}_{signal:%Y%m%d}.jsonl"
        )
        facts_path.parent.mkdir(parents=True, exist_ok=True)
        for index, at in enumerate((entry, exit_)):
            bid, ask = (9990, 10000) if index == 0 else (10050, 10060)
            fact = dict(
                schema="prospective_registered_seed_market_facts_v1",
                symbol=code,
                observed_at_kst=at.isoformat(),
                market_venue="KRX",
                market_session="KRX_REGULAR",
                source_quality_status="PASS",
                advisory_generated=False,
                observation_role="prospective_registered_seed_market_fact",
                seed_memberships=[
                    {
                        key: revision[key]
                        for key in ("revision_sha256", "parameters_sha256", "frozen_at")
                    }
                ],
                bbo=dict(
                    best_bid=bid,
                    best_ask=ask,
                    best_bid_qty=100,
                    best_ask_qty=100,
                    received_at=at.isoformat(),
                    source_epoch=1,
                    source_sequence=index + 1,
                ),
                **loop.AUTHORITY,
            )
            with facts_path.open("a") as handle:
                handle.write(json.dumps(fact) + "\n")
    result = dict(
        name="New causal symbol",
        selected_policy=parameters,
        candidate_revision=revision,
        decision="holdout_pass_widget_signal_policy_candidate",
        runtime_effect=False,
        allowed_runtime_apply=False,
        prospective_window=loop.prospective_window(
            revision, source_date=completed_day, qualified_dates=cal + hold
        ),
    )
    for name, days in dict(
        calibration=cal,
        calibration_first_half=cal[:5],
        calibration_second_half=cal[5:],
        holdout=hold,
    ).items():
        rows = [row for row in selected_rows if row["trade_date"] in days]
        result[name] = {
            **widget._summarize_episodes(rows),
            **economics.modeled_summary(rows, [date.fromisoformat(d) for d in days]),
            "episodes": rows,
        }
    report.update(
        end_date=str(completed_day),
        symbol_universe={**widget.SYMBOLS, code: "New causal symbol"},
        symbol_origins={
            **{symbol: "established_widget_symbol" for symbol in widget.SYMBOLS},
            code: "causal_scanner_research_admission",
        },
        symbols={
            **{
                symbol: dict(
                    name=name,
                    decision="hold_sample_insufficient_signal",
                    runtime_effect=False,
                    allowed_runtime_apply=False,
                )
                for symbol, name in widget.SYMBOLS.items()
            },
            code: result,
        },
        closed_loop_contract=loop.SCHEMA,
        source_meta={
            **report["source_meta"],
            code: dict(
                symbol=code,
                request_code=code,
                market="KRX_regular",
                source_quality_status="PASS",
                daily_source_coverage={"qualified_dates": cal + hold},
            ),
        },
        execution_quality_by_symbol={
            code: load_execution_incidents(
                code,
                target_date=completed_day,
                session="KRX_REGULAR",
                event_dir=tmp_path / "events",
            )
        },
    )
    peer = dict(
        schema=episode.REPORT_SCHEMA,
        target_date=str(completed_day),
        end_date=str(completed_day),
        start_date="2026-06-05",
        status="no_qualified_candidate",
        profiles={},
        recommendations=[],
        postclose_logic_recommendations=[],
        recommendation_count=0,
        trading_date_count=72,
        calibration_trading_day_count=56,
        holdout_trading_day_count=16,
        closed_loop_contract=loop.SCHEMA,
        **loop.AUTHORITY,
    )
    owner_path = tmp_path / "owner.json"
    owner = build_symbol_owner_policy_payload(
        active_date=completed_day,
        policy_id="fixture_owner",
        generated_at_kst=clock[0].isoformat(),
        symbol_entries={
            "999999": dict(mode="EXCLUSIVE_MANUAL", allowed_owners=["manual_operator"])
        },
    )
    loop.atomic_write(owner_path, owner)
    monkeypatch.setattr(funding, "policy_path", lambda day: owner_path)
    source_dir = directory / "native_capacity" / str(completed_day)
    funding.publish_inventory_context(
        dict(
            captured_at=(clock[0] - timedelta(seconds=1)).timestamp(),
            successful_exchanges={"KRX", "NXT"},
            inventory_by_code={},
            open_qty_by_code={},
            open_orders_request_succeeded=True,
        ),
        directory=source_dir,
    )
    funding.publish_cash_context(
        dict(
            kt00011_cash_orderable_contract_status="valid",
            kt00011_capacity_observed_at=clock[0].isoformat(),
            kt00011_capacity_source_sha256="b" * 64,
            account_deposit=2000000,
            cash_orderable_amount=2000000,
            cash_orderable_qty_cap=100,
            kt00011_requested_stock_code="005930",
            kt00011_capacity_contract_version=1,
        ),
        directory=source_dir,
    )
    acq = dict(
        status="complete",
        source_date=str(completed_day),
        native_cash_sha256=loop.read_object(source_dir / "native_cash.json")[
            "native_sha256"
        ],
        native_inventory_sha256=loop.read_object(source_dir / "native_inventory.json")[
            "native_sha256"
        ],
        **loop.AUTHORITY,
    )
    loop.atomic_write(
        directory / f"capacity_source_{completed_day}.json",
        {**acq, "receipt_sha256": loop.digest(acq)},
    )
    loop.atomic_write(
        root
        / "machine_entry_timing_tuning"
        / f"machine_entry_timing_tuning_{completed_day}.json",
        dict(
            target_date=str(completed_day),
            runtime_effect=False,
            same_stage_owner_guard={"mutation_present": False, "status": "clear"},
        ),
    )
    with loop.research_scope(directory):
        result["execution_feasibility"] = economics.signal_execution_feasibility(
            result,
            symbol=code,
            source_date=completed_day,
            signal_policy=publisher._normalized_selected_parameters(parameters)[
                "signal_policy"
            ],
            observation_dir=tmp_path / "absent_legacy",
        )
        assert result["execution_feasibility"]["status"] == "pass", result[
            "execution_feasibility"
        ]
        widget.write_report(
            report, output_dir=root / "widget_symbol_signal_policy_research"
        )
        episode.write_report(
            peer, output_dir=root / "low_price_two_leg_expanded_candidate_research"
        )
    receipt = phase.refresh(completed_day, directory=directory, report_root=root)
    assert receipt["publications"]["widget"]["profile_count"] == 1
    assert receipt["joint_allocation_gate"]["status"] == "pass"
    assert receipt["economic_acceptance"] == "waiting_mature_exact_cost_outcomes"
    assert receipt["actual_order_submitted"] is False
    policy_dir = directory.parent / "widget_symbol_runtime_policy"
    consumer = publisher.WidgetSymbolRuntimePolicyLoader(
        policy_dir, research_dir=root / "widget_symbol_signal_policy_research"
    )
    with loop.research_scope(directory):
        assert code in consumer.resolve_all(
            observed_date=date.fromisoformat(
                receipt["publications"]["widget"]["effective_date"]
            )
        )
    result["holdout"]["notional_weighted_ev_pct"] = 999
    assert not loop.widget_prospective_summary_valid(result, revision)


def test_exact_widget_cost_survives_retry_but_changed_native_fill_cannot_reuse_it(
    tmp_path,
):
    from src.engine.monitoring.research_version_outcomes import collect_widget_outcomes

    version = "a" * 64
    base = dict(
        signal_id="native-signal",
        execution_policy_content_sha256=version,
        order_date=str(DAY),
        filled_qty=10,
        requested_qty=10,
        remaining_qty=0,
        status="FILLED",
        last_reconciled_at=f"{DAY}T12:02:00+09:00",
    )
    buy = dict(base, order_no="B1", side="BUY", fill_price=10000)
    sell = dict(
        base,
        order_no="S1",
        side="SELL",
        fill_price=10050,
        parent_entry_signal_id="native-signal",
    )
    state = dict(active_date=str(DAY), symbols={"000001": {"orders": [buy, sell]}})
    path = tmp_path / "state.json"
    loop.atomic_write(path, state)
    broker = lambda day, symbol: [
        dict(
            filled_qty=10,
            buy_average_price=10000,
            sell_average_price=10050,
            realized_net_profit_krw=270,
            commission_krw=30,
            tax_krw=200,
        )
    ]
    first = collect_widget_outcomes(
        DAY, state_path=path, directory=tmp_path, loader=broker
    )
    assert first["rows"][0]["realized_net_profit_krw"] == 270
    resumed = collect_widget_outcomes(DAY, state_path=path, directory=tmp_path)
    assert resumed["rows"][0]["realized_net_profit_krw"] == 270
    sell["fill_price"] = 10060
    loop.atomic_write(path, state)
    changed = collect_widget_outcomes(DAY, state_path=path, directory=tmp_path)
    assert changed["rows"][0]["realized_net_profit_krw"] is None


def test_episode_cf_requires_both_original_legs_and_sufficient_shared_depth(tmp_path):
    from datetime import timedelta
    from src.engine.monitoring.episode_prospective_research import execution_feasibility
    from src.trading.low_price_two_leg.economics import cost_contract

    params = dict(entry_valid_completed_bars=1)
    revision = loop.candidate_revision(
        symbol="000001",
        owner="episode",
        lane_id="new_symbol",
        parameters=params,
        source_date=DAY,
        source_sha256="a" * 64,
        cost_sha256=loop.digest(cost_contract()),
        calibration_days=30,
        holdout_days=16,
        frozen_at=datetime.fromisoformat(f"{DAY}T20:10:00+09:00"),
    )
    signal = datetime.fromisoformat(revision["holdout_dates"][0] + "T12:00:00+09:00")
    entry, exit_ = signal + timedelta(minutes=1), signal + timedelta(minutes=2)
    leg = dict(
        status="COMPLETE",
        fill_at=entry.isoformat(),
        target_at=exit_.isoformat(),
        entry_price=10000,
        target_price=10100,
        net_profit_pct=1 - cost_contract()["round_trip_cost_pct"],
    )
    result = dict(
        symbol="000001",
        candidate_revision=revision,
        selected=dict(
            parameters=params,
            full=dict(
                episodes=[
                    dict(signal_at=signal.isoformat(), legs=[dict(leg), dict(leg)])
                ]
            ),
        ),
    )
    path = tmp_path / "facts" / f"prospective_facts_000001_{signal:%Y%m%d}.jsonl"
    path.parent.mkdir()
    rows = []
    for seq, at, bid, ask in ((1, entry, 9990, 10000), (2, exit_, 10100, 10110)):
        rows.append(
            dict(
                schema="prospective_registered_seed_market_facts_v1",
                source_quality_status="PASS",
                market_venue="KRX",
                observed_at_kst=at.isoformat(),
                seed_memberships=[
                    dict(
                        revision_sha256=revision["revision_sha256"],
                        parameters_sha256=revision["parameters_sha256"],
                        frozen_at=revision["frozen_at"],
                    )
                ],
                bbo=dict(
                    received_at=at.isoformat(),
                    best_bid=bid,
                    best_ask=ask,
                    best_bid_qty=100,
                    best_ask_qty=100,
                    source_epoch=1,
                    source_sequence=seq,
                ),
                **loop.AUTHORITY,
            )
        )
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    day = date.fromisoformat(revision["holdout_dates"][-1])
    proof = execution_feasibility(result, source_date=day, directory=tmp_path)
    assert proof["status"] == "pass" and proof["matched_completed_legs"] == 2
    for row in rows:
        row["bbo"]["best_ask_qty"] = 60
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    assert (
        execution_feasibility(result, source_date=day, directory=tmp_path)["reason"]
        == "shared_depth_insufficient_for_full_stress_quantity"
    )
    result["selected"]["full"]["episodes"][0]["legs"][1]["status"] = "HELD"
    for row in rows:
        row["bbo"]["best_ask_qty"] = 100
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    assert (
        execution_feasibility(result, source_date=day, directory=tmp_path)["reason"]
        == "partial_held_or_censored_leg"
    )


def test_native_decision_checkpoint_resume_deduplicates_and_preserves_asof(tmp_path):
    from datetime import timedelta
    from src.trading.widget_auto_trade.engine import WidgetTradeEventRecorder

    now = datetime.fromisoformat(f"{DAY}T12:00:00+09:00")
    event = dict(
        symbol="000001",
        signal_id=f"000001:{DAY}:ENTRY:1",
        execution_policy_content_sha256="a" * 64,
        event_type="entry_guard_blocked",
        actual_order_submitted=False,
    )
    recorder = WidgetTradeEventRecorder(tmp_path)
    recorder.record(event, now)
    destination = tmp_path / f"research_decisions_{DAY}.json"
    first = loop.read_object(destination)
    recorder.record(event, now + timedelta(seconds=1))
    recovered = WidgetTradeEventRecorder(tmp_path)
    recovered.record(event, now + timedelta(seconds=31))
    summary = loop.read_object(destination)
    assert len(summary["native_decisions"]) == 1
    event_path = tmp_path / f"widget_signal_auto_trade_events_{DAY:%Y%m%d}.jsonl"
    recovered._record_research_decision({}, now + timedelta(seconds=62), event_path)
    assert loop.read_object(destination) == summary
    assert first["status"] == "complete" and summary["actual_order_submitted"] is False


def test_seed_readers_share_bounded_immutable_point_decode(tmp_path):
    from datetime import timedelta

    at = datetime.fromisoformat(f"{DAY}T12:00:00+09:00")
    path = tmp_path / "facts.jsonl"
    path.write_text(
        json.dumps(dict(observed_at_kst=at.isoformat(), bbo=dict(best_ask=100))) + "\n"
    )
    before = facts.COUNTERS["point_decodes"]
    first = facts.indexed_day_facts(path, windows=[(at, at + timedelta(seconds=1))])
    for _ in range(3):
        assert (
            facts.indexed_day_facts(path, windows=[(at, at + timedelta(seconds=1))])
            == first
        )
    assert facts.COUNTERS["point_decodes"] == before + 1
    with pytest.raises(TypeError):
        first[1][0]["bbo"]["best_ask"] = 0
    assert facts._CACHE_BYTES <= facts.MAX_CACHE_BYTES
    path.write_text(
        json.dumps(dict(observed_at_kst=at.isoformat(), bbo=dict(best_ask=101))) + "\n"
    )
    assert (
        facts.indexed_day_facts(path, windows=[(at, at + timedelta(seconds=1))])[0]
        != first[0]
    )
    assert facts.COUNTERS["point_decodes"] == before + 2


def _native_episode_prospective_fixture():
    from datetime import timedelta
    from src.engine.monitoring import episode_prospective_research as prospective
    from src.engine.monitoring import low_price_two_leg_entry_spot_research as native
    from src.trading.low_price_two_leg.economics import cost_contract

    parameters = dict(
        scan_start="10:05",
        scan_end="10:59",
        lookback_bars=20,
        rolling_high_drawdown_pct=0.5,
        rolling_low_proximity_pct=0.2,
        entry_offsets_ticks=[0, -1],
        entry_valid_completed_bars=5,
        target_ticks=5,
    )
    baseline = {**parameters, "rolling_high_drawdown_pct": 9.0}
    revision = loop.candidate_revision(
        symbol="000001",
        owner="episode",
        lane_id="new_000001_late_morning",
        parameters=parameters,
        baseline_parameters=baseline,
        source_date=DAY,
        source_sha256="a" * 64,
        cost_sha256=loop.digest(cost_contract()),
        calibration_days=30,
        holdout_days=16,
        frozen_at=datetime.fromisoformat(f"{DAY}T20:10:00+09:00"),
    )
    cal = [date.fromisoformat(day) for day in revision["calibration_dates"]]
    hold = [date.fromisoformat(day) for day in revision["holdout_dates"]]
    contexts = {}
    for day in cal + hold:
        signal = datetime.fromisoformat(f"{day}T10:05:00+09:00")
        bars = (
            native.Bar(signal, 10000, 10000, 10000, 10000),
            native.Bar(signal + timedelta(minutes=1), 10000, 10000, 9980, 10000),
            native.Bar(signal + timedelta(minutes=2), 10000, 10060, 10000, 10050),
        )
        contexts[day] = native.DayContext(
            day, bars, {20: (native.SignalFeature(0, signal, 10000, 1.0, 0.0),)}
        )
    windows = dict(
        calibration=cal,
        calibration_first_half=cal[:15],
        calibration_second_half=cal[15:],
        holdout=hold,
        full=cal + hold,
    )
    result = dict(symbol="000001", candidate_revision=revision)
    for name, params in (("selected", parameters), ("baseline", baseline)):
        summaries = native._evaluate_candidate_windows(
            prospective.spot(params),
            contexts,
            list(windows.values()),
            include_episodes=True,
        )
        result[name] = dict(parameters=params, **dict(zip(windows, summaries)))
    result["paired_economics"] = native.paired_economics(
        result["baseline"]["holdout"], result["selected"]["holdout"]
    )
    result["prospective_qualified_dates"] = [str(day) for day in cal + hold]
    result["prospective_window"] = loop.prospective_window(
        revision, source_date=hold[-1], qualified_dates=cal + hold
    )
    return result, revision, hold[-1]


@pytest.mark.parametrize(
    "mutation",
    ["ev", "half_samples", "paired", "baseline", "duplicate", "price", "cost"],
)
def test_episode_promotion_reconstructs_native_window_economics(mutation):
    from src.engine.monitoring.episode_prospective_research import (
        prospective_summary_valid,
    )

    result, revision, _ = _native_episode_prospective_fixture()
    assert prospective_summary_valid(result, revision)
    if mutation == "ev":
        result["selected"]["holdout"]["notional_weighted_ev_pct"] += 10
    elif mutation == "half_samples":
        result["selected"]["calibration_first_half"]["completed_legs"] = 0
    elif mutation == "paired":
        result["paired_economics"]["net_profit_uplift_krw_per_observation_day"] = 10000
    elif mutation == "baseline":
        result["baseline"]["holdout"]["realized_net_profit_krw"] = -99999
    elif mutation == "duplicate":
        result["selected"]["full"]["episodes"].append(
            deepcopy(result["selected"]["full"]["episodes"][0])
        )
    elif mutation == "price":
        result["selected"]["holdout"]["episodes"][0]["legs"][0]["entry_price"] += 10
    else:
        result["selected"]["holdout"]["episodes"][0]["legs"][0]["net_profit_pct"] += (
            0.23
        )
    assert not prospective_summary_valid(result, revision)


def test_episode_native_cf_publication_and_reader_recheck_summary(
    tmp_path, monkeypatch
):
    from datetime import timedelta
    from src.engine.monitoring import episode_prospective_research as prospective
    from src.engine.automation import (
        low_price_two_leg_auto_expansion_policy as publisher,
    )
    from src.engine.monitoring.machine_recommendation_identity import (
        bind_recommendation,
    )
    from src.tests.test_machine_candidate_auto_expansion import _report

    result, revision, day = _native_episode_prospective_fixture()
    directory = tmp_path / "research"
    loop.freeze_candidate(revision, directory=directory)
    from contextvars import ContextVar

    monkeypatch.setattr(
        loop, "_RESEARCH_SCOPE", ContextVar("episode_test_scope", default=directory)
    )
    monkeypatch.setattr(
        prospective,
        "execution_feasibility",
        (
            lambda value, *, source_date, native=prospective.execution_feasibility: (
                native(value, source_date=source_date, directory=directory)
            )
        ),
    )

    class NativeClock(datetime):
        @classmethod
        def now(cls, tz=None):
            clock = datetime.fromisoformat(f"{day}T20:10:00+09:00")
            return clock.astimezone(tz) if tz else clock

    monkeypatch.setattr(loop, "datetime", NativeClock)
    for episode in result["selected"]["full"]["episodes"]:
        signal = datetime.fromisoformat(episode["signal_at"])
        rows = []
        for seq, at, bid, ask in (
            (1, signal + timedelta(minutes=1), 9980, 9990),
            (2, signal + timedelta(minutes=2), 10050, 10060),
        ):
            rows.append(
                dict(
                    schema="prospective_registered_seed_market_facts_v1",
                    source_quality_status="PASS",
                    market_venue="KRX",
                    observed_at_kst=at.isoformat(),
                    seed_memberships=[
                        dict(
                            revision_sha256=revision["revision_sha256"],
                            parameters_sha256=revision["parameters_sha256"],
                            frozen_at=revision["frozen_at"],
                        )
                    ],
                    bbo=dict(
                        received_at=at.isoformat(),
                        best_bid=bid,
                        best_ask=ask,
                        best_bid_qty=100,
                        best_ask_qty=100,
                        source_epoch=1,
                        source_sequence=seq,
                    ),
                    **loop.AUTHORITY,
                )
            )
        path = directory / "facts" / f"prospective_facts_000001_{signal:%Y%m%d}.jsonl"
        path.parent.mkdir(exist_ok=True)
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    proof = prospective.execution_feasibility(result, source_date=day)
    assert proof["status"] == "pass" and proof["matched_completed_legs"] == 92
    result["execution_feasibility"] = proof
    report = _report()
    row = report["recommendations"][0]
    row.update(
        profile_id=revision["lane_id"],
        symbol="000001",
        discovery_lane="new_symbol",
        recommended_spot=revision["parameters"],
        paired_economics=result["paired_economics"],
        current_economic_outcome=result["baseline"]["holdout"],
        candidate_economic_outcome=result["selected"]["holdout"],
    )
    for key in list(row):
        if key.startswith("recommendation_"):
            del row[key]
    bind_recommendation(
        row,
        producer="low_price_two_leg_expanded_candidate_research",
        scope="000001/late_morning/new_000001_late_morning",
        axis="profile_policy",
        proposal=revision["parameters"],
        consumer="low_price_two_leg_policy_apply",
        acceptance="native CF fixture",
    )
    joint = dict(status="pass")
    # Native capital reconstruction has its separate widget/joint positive E2E;
    # isolate this episode publisher/reader semantic boundary here.
    monkeypatch.setattr(loop, "combined_joint_gate", lambda *a, **kw: joint)
    report.update(
        target_date=str(day),
        closed_loop_contract=loop.SCHEMA,
        profiles={revision["lane_id"]: result},
        joint_allocation_gate=joint,
    )
    report_dir, policy_dir = tmp_path / "reports", tmp_path / "policies"
    source = report_dir / f"low_price_two_leg_expanded_candidate_research_{day}.json"
    loop.atomic_write(source, report)
    payload = publisher.build_policy(
        source_date=day, report_dir=report_dir, policy_dir=policy_dir
    )
    assert "auto_000001_late_morning" in payload["profiles"]
    effective = date.fromisoformat(payload["effective_date"])
    path = publisher.policy_path(effective, policy_dir=policy_dir)
    loop.publication_transaction(
        policy_dir,
        effective_date=effective,
        files={path.name: payload},
        expected_generation=None,
    )
    assert (
        publisher.load_policy(effective, policy_dir=policy_dir)["profiles"][
            "auto_000001_late_morning"
        ]["policy"]
        == revision["parameters"]
    )
    report["profiles"][revision["lane_id"]]["selected"]["holdout"]["completed_legs"] = 1
    loop.atomic_write(source, report)
    rejected = publisher.build_policy(
        source_date=day, report_dir=report_dir, policy_dir=tmp_path / "fresh"
    )
    assert "auto_000001_late_morning" not in rejected["profiles"]
    # Even a self-consistent signed source/publication cannot bypass the
    # consumer's independent sample/economic reconstruction.
    payload["source_report_sha256"] = publisher._file_sha256(source)
    payload["policy_hash"] = publisher._digest(
        {key: value for key, value in payload.items() if key != "policy_hash"}
    )
    forged_dir = tmp_path / "forged"
    loop.publication_transaction(
        forged_dir,
        effective_date=effective,
        files={path.name: payload},
        expected_generation=None,
    )
    with pytest.raises(ValueError, match="episode_closed_loop_reconstruction_invalid"):
        publisher.load_policy(effective, policy_dir=forged_dir)


def test_scale_cli_honors_phase_and_compute_budget(tmp_path, monkeypatch):
    from src.engine.monitoring import research_scale_benchmark as benchmark

    def bounded_run(symbol_count, day_count, cache, output, **options):
        assert symbol_count == 100 and day_count == 120
        assert options["modes"] == ("cold",)
        assert options["compute_budget_sec"] == 17
        return dict(status="deferred")

    monkeypatch.setattr(benchmark, "run", bounded_run)
    assert (
        benchmark.main(
            [
                "--symbols",
                "100",
                "--days",
                "120",
                "--modes",
                "cold",
                "--compute-budget-sec",
                "17",
                "--output",
                str(tmp_path / "receipt.json"),
            ]
        )
        == 75
    )


def test_scale_cli_defaults_are_bounded_not_full_expansion(tmp_path, monkeypatch):
    from src.engine.monitoring import research_scale_benchmark as benchmark

    def bounded_run(symbol_count, day_count, cache, output, **options):
        assert (symbol_count, day_count) == (3, 46)
        assert options["modes"] == ("cold", "warm", "append")
        assert options["compute_budget_sec"] == 300
        return dict(status="complete")

    monkeypatch.setattr(benchmark, "run", bounded_run)
    assert benchmark.main(["--output", str(tmp_path / "receipt.json")]) == 0


@pytest.mark.parametrize("budget", ["0", "-1"])
def test_scale_cli_rejects_nonpositive_budget_before_compute(tmp_path, monkeypatch, budget):
    from src.engine.monitoring import research_scale_benchmark as benchmark

    def forbidden(*args, **kwargs):
        raise AssertionError("invalid fixture budget must not start replay")

    monkeypatch.setattr(benchmark, "run", forbidden)
    with pytest.raises(ValueError, match="benchmark_fixture_shape_invalid"):
        benchmark.main(["--output", str(tmp_path / "receipt.json"), "--compute-budget-sec", budget])


def test_episode_scale_cli_defaults_are_bounded(tmp_path, monkeypatch):
    from analysis.benchmarks import widget_episode_incremental_scale as benchmark

    def bounded_run(symbols, days, output, cache, budget):
        assert (symbols, days, budget) == (3, 46, 300)
        return dict(status="complete")

    monkeypatch.setattr(benchmark, "run", bounded_run)
    assert benchmark.main(["--output", str(tmp_path / "receipt.json")]) == 0


@pytest.mark.parametrize('captured_at', ['2026-09-17T20:04:59+09:00', '2026-09-18T20:05:00+09:00'])
def test_native_capacity_rejects_wrong_clock_before_account_or_token_helpers(tmp_path, monkeypatch, captured_at):
    from types import SimpleNamespace
    from src.engine.monitoring import research_native_capacity_source as source
    captured = datetime.fromisoformat(captured_at)
    monkeypatch.setattr(source, 'datetime', SimpleNamespace(now=lambda tz: captured))
    def forbidden(*a, **kw):
        pytest.fail('account helper called before dated source preflight')
    adapters = dict.fromkeys(('inventory', 'unfilled', 'deposit', 'deposit_meta', 'capacity'), forbidden)
    result = source.acquire(date(2026,9,17), directory=tmp_path, token='fixture', adapters=adapters)
    assert result['status'] == 'source_gap'
    assert result['reason'] == 'native_source_requires_current_completed_date_after_20_05'
    assert not (tmp_path/'native_capacity').exists()
