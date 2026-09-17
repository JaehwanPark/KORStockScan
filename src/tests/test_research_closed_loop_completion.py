"""Regression contracts for the remaining research/selection/cache closure."""

from copy import deepcopy
from dataclasses import replace
from datetime import date, datetime
import subprocess
import sys

import pytest
from src.engine.monitoring import research_closed_loop as loop
from src.engine.monitoring import research_cache_storage as storage
from src.engine.monitoring import research_portfolio_economics as portfolio
from src.engine.monitoring import research_version_outcomes as outcomes
from src.engine.monitoring import low_price_two_leg_entry_spot_research as spot
from src.engine.monitoring import (
    low_price_two_leg_expanded_candidate_research as expanded,
)
from src.tests.test_low_price_two_leg_entry_spot_research import _contexts


def _bucket(count, net=-0.2):
    return dict(
        exact_completed_count=count,
        realized_net_return_pct=net,
        realized_buy_notional_krw=10000,
    )


def test_version_feedback_shared_alias_preserves_native_identity(tmp_path):
    native = tmp_path / "native"
    native.mkdir()
    alias = tmp_path / "release_data_alias"
    alias.symlink_to(native, target_is_directory=True)
    day = date(2026, 9, 17)
    body = dict(source_date=str(day), rows=[], **loop.AUTHORITY)
    loop.atomic_write(
        native / f"widget_outcomes_{day}.json",
        dict(body, outcomes_sha256=loop.digest(body)),
    )
    assert outcomes.outcome_feedback(
        day, directory=native
    ) == outcomes.outcome_feedback(day, directory=alias)


@pytest.mark.parametrize(
    "full,tail,expected",
    [
        (_bucket(6), _bucket(4), True),
        (_bucket(5), _bucket(4), False),
        (_bucket(6), _bucket(3), False),
        (_bucket(6, 0.2), _bucket(4), False),
        (_bucket(6), _bucket(4, float("nan")), False),
        (_bucket(6), _bucket(4, None), False),
    ],
)
def test_widget_retirement_uses_mature_exact_original_revision(full, tail, expected):
    feedback = dict(
        cumulative=dict(strategy_revisions={"a" * 64: full}),
        holdout_last_16=dict(strategy_revisions={"a" * 64: tail}),
    )
    assert outcomes.mature_widget_retired_revisions(feedback) == (
        {"a" * 64} if expected else set()
    )


def _reference(candidate_net=0.3, baseline_net=0.2):
    dates = loop.trading_dates_after(date(2026, 6, 4), 26)

    def row(day, net):
        return dict(
            entry_at=day + "T09:10:00+09:00",
            exit_at=day + "T09:15:00+09:00",
            entry_price=10000,
            net_return_pct=net,
        )

    lane = {}
    for name, days in [("calibration", dates[:10]), ("holdout", dates[10:])]:
        lane[name + "_dates"] = days
        lane["candidate_" + name] = [row(day, candidate_net) for day in days]
        lane["incumbent_" + name] = [row(day, baseline_net) for day in days]
    return [
        dict(
            portfolio_reference=dict(
                lanes={"widget:000001": lane}, missing_reference_lanes=[]
            )
        )
    ]


def _funding():
    return dict(
        available_cash_krw=1000000,
        reserved_notional_krw=0,
        exposure_limit_krw=1000000,
        holding_notional_krw=0,
        constraints=dict(buy_fee_bps=5),
    )


@pytest.mark.parametrize(
    "candidate,baseline,expected",
    [
        (0.3, 0.2, "pass"),
        (0.1, 0.2, "allocation_blocked"),
        (-0.1, 0.0, "allocation_blocked"),
    ],
)
def test_joint_gate_checks_original_portfolio_profit_and_calendar(
    candidate, baseline, expected
):
    result = portfolio.paired_joint_economics(
        _reference(candidate, baseline), _funding()
    )
    assert result["status"] == expected
    assert len(result["windows"]["holdout"]["candidate"]["observation_dates"]) == 16
    assert result["windows"]["holdout"]["candidate"]["capital_krw_minutes"] == 8000000
    assert result["runtime_effect"] is False


@pytest.mark.parametrize(
    "mutation",
    ["cost", "missing_reference", "duplicate", "missing_net", "future_exit", "tail"],
)
def test_joint_incomplete_or_degraded_reference_cannot_promote(mutation):
    inputs, funding = _reference(), _funding()
    lane = inputs[0]["portfolio_reference"]["lanes"]["widget:000001"]
    if mutation == "cost":
        funding["constraints"]["buy_fee_bps"] = None
    elif mutation == "missing_reference":
        inputs[0]["portfolio_reference"]["missing_reference_lanes"] = ["000002"]
    elif mutation == "duplicate":
        inputs.append(deepcopy(inputs[0]))
    elif mutation == "missing_net":
        lane["candidate_holdout"][0]["net_return_pct"] = None
    elif mutation == "future_exit":
        lane["candidate_holdout"][0]["exit_at"] = "2026-12-31T09:15:00+09:00"
    else:
        lane["candidate_holdout"][0]["net_return_pct"] = -0.3
    assert (
        portfolio.paired_joint_economics(inputs, funding)["status"]
        == "allocation_blocked"
    )


@pytest.mark.parametrize("legs", [None, [], [{"status": "COMPLETE"}], [None, None]])
def test_episode_joint_reference_rejects_missing_native_two_leg_outcome(legs):
    revision = loop.candidate_revision(
        symbol="007660",
        parameters={},
        owner="episode",
        calibration_days=30,
        source_date=date(2026, 6, 5),
        source_sha256="a" * 64,
        cost_sha256="b" * 64,
        frozen_at=datetime.fromisoformat("2026-06-05T21:30:00+09:00"),
    )
    report = dict(
        profiles={
            "candidate_007660_midday": dict(
                decision="holdout_pass_source_only_early_candidate",
                candidate_revision=revision,
                selected=dict(
                    calibration=dict(episodes=[dict(legs=legs)]),
                    holdout=dict(episodes=[]),
                ),
                baseline=dict(calibration=dict(episodes=[]), holdout=dict(episodes=[])),
            )
        }
    )
    with pytest.raises(ValueError, match="partial_held_or_missing_leg"):
        portfolio.reference_inputs(report, "episode")


def _cached_windows(directory, contexts, windows, candidate, stats):
    profile = expanded.RESEARCH_PROFILES["candidate_007660_midday"]
    transitions = expanded._DayStateCheckpoint(profile, contexts, directory, stats)
    with spot.day_replay_scope(transitions):
        return spot._evaluate_candidate_windows(
            candidate, contexts, windows, include_episodes=True
        )


@pytest.mark.parametrize("net", [0.2, -0.2])
def test_episode_append_and_partition_reuses_days_preserving_original_holding(
    tmp_path, net
):
    contexts = _contexts(holdout_candidate_net=net, total_days=47)
    profile = expanded.RESEARCH_PROFILES["candidate_007660_midday"]
    candidate = spot.baseline_candidate(profile)
    days = sorted(contexts)
    windows = [days[:30], days[30:46]]
    stats = {}
    expected = spot._evaluate_candidate_windows(
        candidate, deepcopy(contexts), windows, include_episodes=True
    )
    actual = _cached_windows(
        tmp_path / "states" / "symbol", deepcopy(contexts), windows, candidate, stats
    )
    assert actual == expected and stats["day_replay"] == 46
    warm = {}
    assert (
        _cached_windows(
            tmp_path / "states" / "symbol", deepcopy(contexts), windows, candidate, warm
        )
        == expected
    )
    assert warm == {"day_hit": 46}
    moved = [days[:31], days[31:47]]
    appended = {}
    expected = spot._evaluate_candidate_windows(
        candidate, deepcopy(contexts), moved, include_episodes=True
    )
    assert (
        _cached_windows(
            tmp_path / "states" / "symbol",
            deepcopy(contexts),
            moved,
            candidate,
            appended,
        )
        == expected
    )
    assert appended == {"day_hit": 46, "day_replay": 1}
    changed = deepcopy(contexts)
    d = days[5]
    changed[d].features[30] = tuple(
        replace(feature, drawdown_pct=feature.drawdown_pct + 0.01)
        for feature in changed[d].features[30]
    )
    fixed = {}
    reference = spot._evaluate_candidate_windows(
        candidate, deepcopy(changed), moved, include_episodes=True
    )
    assert (
        _cached_windows(
            tmp_path / "states" / "symbol", changed, moved, candidate, fixed
        )
        == reference
    )
    assert fixed["day_replay"] >= 1


def test_dead_process_lru_preserves_reader_and_required_raw(tmp_path):
    root = tmp_path / "cache"
    raw = tmp_path / "raw.jsonl"
    raw.write_text("required\n")
    script = """from pathlib import Path
from src.engine.monitoring import research_closed_loop as loop
import sys
root=Path(sys.argv[1])
assert loop.optional_cache_write(root/'a'/'day.json.z',b'aaaaaa',cache_root=root,soft_cap=12,reserve=0)
assert loop.optional_cache_write(root/'b'/'day.json.z',b'bbbbbb',cache_root=root,soft_cap=12,reserve=0)
"""
    subprocess.run([sys.executable, "-c", script, str(root)], check=True)
    assert storage.touch(root / "a" / "day.json.z", root=root)
    assert loop.optional_cache_write(
        root / "c" / "day.json.z", b"cccccc", cache_root=root, soft_cap=12, reserve=0
    )
    assert (root / "a" / "day.json.z").read_bytes() == b"aaaaaa"
    assert not (root / "b" / "day.json.z").exists()
    assert raw.read_text() == "required\n"
    assert loop.read_object(root / ".optional_cache_bytes.json")["charged_bytes"] == 12


def test_cache_symlink_and_corrupt_catalog_never_remove_evidence(tmp_path):
    root = tmp_path / "cache"
    root.mkdir()
    required = tmp_path / "raw"
    required.write_bytes(b"keep")
    (root / "unsafe").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError):
        loop.optional_cache_write(
            root / "unsafe" / "raw.json.z", b"x", cache_root=root, soft_cap=4, reserve=0
        )
    (root / ".optional_cache_catalog.sqlite3").write_bytes(b"corrupt")
    with pytest.raises(ValueError):
        loop.optional_cache_write(
            root / "a" / "day.json.z", b"x", cache_root=root, soft_cap=4, reserve=0
        )
    assert required.read_bytes() == b"keep"


def test_optional_deep_json_is_safe_miss_without_removing_source(tmp_path, monkeypatch):
    import json
    import zlib

    root = tmp_path / "cache"
    path = root / "profile" / "day.json.z"
    original = tmp_path / "required-source"
    original.write_bytes(b"preserve")
    raw = zlib.compress(b"[" * 2000 + b"0" + b"]" * 2000)
    assert loop.optional_cache_write(path, raw, cache_root=root, reserve=0)

    def parser_recursion(payload):
        assert payload == zlib.decompress(raw)
        raise RecursionError("fixture parser recursion limit")

    monkeypatch.setattr(json, "loads", parser_recursion)
    assert storage.read(path, root=root) is None
    assert original.read_bytes() == b"preserve"
    assert path.read_bytes() == raw


def test_optional_catalog_transaction_error_does_not_abort_reader(tmp_path, monkeypatch):
    import sqlite3

    root = tmp_path / "cache"
    original = tmp_path / "required-source"
    original.write_bytes(b"preserve")

    class BrokenConnection:
        def execute(self, *_args):
            raise sqlite3.OperationalError("database is locked")

        def close(self):
            pass

    monkeypatch.setattr(storage, "_catalog", lambda _root: storage._Catalog(BrokenConnection()))
    assert storage.read(root / "profile" / "day.json.z", root=root) is None
    with pytest.raises(ValueError, match="optional_cache_catalog_invalid"):
        loop.optional_cache_write(root / "other" / "day.json.z", b"x", cache_root=root, reserve=0)
    assert original.read_bytes() == b"preserve"


def test_native_widget_realized_feedback_retires_incumbent_carry_only(
    tmp_path, monkeypatch
):
    from src.engine.monitoring import widget_symbol_runtime_policy as publisher
    from src.tests.test_widget_symbol_runtime_policy import _research

    today = date(2026, 9, 17)
    revision, version = "a" * 64, "b" * 64
    days = loop.trading_dates_after(date(2026, 9, 8), 7)
    history = []
    for index, day in enumerate(days):
        common = dict(
            signal_id="signal-" + day,
            execution_policy_content_sha256=version,
            candidate_revision_sha256=revision,
            order_date=day,
            filled_qty=10,
            requested_qty=10,
            remaining_qty=0,
            status="FILLED",
            last_reconciled_at=day + "T12:02:00+09:00",
        )
        buy = dict(common, order_no="B" + str(index), side="BUY", fill_price=10000)
        sell = dict(
            common,
            order_no="S" + str(index),
            side="SELL",
            fill_price=9950,
            parent_entry_signal_id=common["signal_id"],
        )
        history.append(
            dict(trade_date=day, symbols={"006800": dict(orders=[buy, sell])})
        )
    state = tmp_path / "state.json"
    loop.atomic_write(state, dict(active_date=str(today), symbols={}, history=history))
    broker = lambda day, symbol: [
        dict(
            filled_qty=10,
            buy_average_price=10000,
            sell_average_price=9950,
            realized_net_profit_krw=-730,
            commission_krw=30,
            tax_krw=200,
        )
    ]
    for native_day in days:
        outcomes.collect_widget_outcomes(
            date.fromisoformat(native_day),
            state_path=state,
            directory=tmp_path,
            loader=broker,
        )
    native = outcomes.outcome_feedback(today, directory=tmp_path)
    assert (
        native["cumulative"]["strategy_revisions"][revision]["exact_completed_count"]
        == 7
    )
    assert outcomes.mature_widget_retired_revisions(native) == {revision}
    report = _research()
    report["end_date"] = str(today)
    report["closed_loop_contract"] = loop.SCHEMA
    report["policy_version_feedback"] = native
    gate = dict(status="allocation_blocked", reason="no_new_candidate")
    report["joint_allocation_gate"] = gate
    monkeypatch.setattr(loop, "report_joint_gate", lambda *args, **kwargs: gate)
    monkeypatch.setattr(outcomes, "outcome_feedback", lambda day: native)
    monkeypatch.setattr(
        publisher.WidgetSymbolRuntimePolicyLoader,
        "resolve_all",
        lambda *args, **kwargs: {"006800": dict(candidate_revision_sha256=revision)},
    )
    policy = publisher.build_policy(report)
    assert "006800" not in policy["symbols"]
    assert policy["retired_candidate_revision_sha256"] == [revision]
    forged = deepcopy(report)
    forged["policy_version_feedback"]["cumulative"]["strategy_revisions"][revision][
        "realized_net_return_pct"
    ] = 1
    with pytest.raises(ValueError, match="native_version_feedback"):
        publisher.build_policy(forged)


def test_cheap_episode_cache_uses_measured_fast_reference_without_reducing_grid(
    tmp_path, monkeypatch
):
    from src.tests.test_low_price_two_leg_expanded_candidate_research import (
        _selection_checkpoint_fixture,
    )

    profile, contexts = _selection_checkpoint_fixture("zero")
    cold = expanded._select_profile_checkpoint(
        profile,
        deepcopy(contexts),
        calibration_days=30,
        cache_dir=tmp_path,
        contract={"generation": "cold"},
    )
    strategy = next(tmp_path.glob(".day_strategy_*.meta"))
    metadata = loop.read_object(strategy)
    metadata["enabled"] = False
    loop.atomic_write(strategy, metadata)

    def forbidden(*args, **kwargs):
        raise AssertionError("disabled optional cache cannot replay cached transitions")

    monkeypatch.setattr(expanded._DayStateCheckpoint, "__call__", forbidden)
    stats = {}
    actual = expanded._select_profile_checkpoint(
        profile,
        deepcopy(contexts),
        calibration_days=30,
        cache_dir=tmp_path,
        contract={"generation": "changed"},
        day_stats=stats,
    )
    assert actual == cold
    assert actual["grid_candidate_count"] == len(spot.candidate_grid(profile))
    assert stats == {"cache_disabled_fast_reference": 1}


@pytest.mark.parametrize("mode", ["zero", "complete", "held"])
def test_cold_probe_stops_after_one_page_and_keeps_entire_native_grid(
    tmp_path, monkeypatch, mode
):
    from src.tests.test_low_price_two_leg_expanded_candidate_research import (
        _selection_checkpoint_fixture,
    )

    profile, contexts = _selection_checkpoint_fixture(mode)
    expected = spot.select_profile_spot(
        profile, deepcopy(contexts), calibration_days=30, holdout_days=16
    )
    native = expanded._DayStateCheckpoint.__call__

    def cheap(self, *args):
        self.native_cpu = 0.0
        return native(self, *args)

    monkeypatch.setattr(expanded._DayStateCheckpoint, "__call__", cheap)
    stats = {}
    actual = expanded._select_profile_checkpoint(
        profile,
        deepcopy(contexts),
        calibration_days=30,
        cache_dir=tmp_path,
        contract={"generation": "cold"},
        day_stats=stats,
    )
    assert actual == expected
    assert actual["grid_candidate_count"] == len(spot.candidate_grid(profile))
    assert stats["probe_aborted_fast_reference"] == 1
    assert stats["day_replay"] <= 16 * len(contexts)
    assert (
        loop.read_object(next(tmp_path.glob(".day_strategy_*.meta")))["enabled"]
        is False
    )


@pytest.mark.parametrize(
    "metadata",
    [
        "{broken",
        "[]",
        '{"evicted_bytes":"bad","written_bytes":false}',
        '{"evicted_bytes":-1,"written_bytes":-5}',
    ],
)
def test_optional_byte_ledger_damage_does_not_abort_cache_write(tmp_path, metadata):
    import json
    import zlib

    root = tmp_path / "cache"
    path = root / "symbol" / "day.json.z"
    required = tmp_path / "native-source"
    required.write_bytes(b"preserve")
    raw = zlib.compress(json.dumps({"rows": []}).encode())
    assert loop.optional_cache_write(path, raw, cache_root=root, reserve=0)
    (root / ".optional_cache_bytes.json").write_text(metadata)
    assert loop.optional_cache_write(path, raw, cache_root=root, reserve=0)
    assert storage.read(path, root=root) == {"rows": []}
    ledger = loop.read_object(root / ".optional_cache_bytes.json")
    assert ledger["charged_bytes"] == len(raw)
    assert ledger["evicted_bytes"] == 0
    assert ledger["written_bytes"] == len(raw)
    assert required.read_bytes() == b"preserve"


def test_optional_byte_ledger_parser_recursion_is_recovered(tmp_path, monkeypatch):
    from pathlib import Path

    root = tmp_path / "cache"
    native = loop.read_object

    def recursive_ledger(path, *args, **kwargs):
        if Path(path).name == ".optional_cache_bytes.json":
            raise RecursionError("damaged optional metadata")
        return native(path, *args, **kwargs)

    monkeypatch.setattr(loop, "read_object", recursive_ledger)
    assert loop.optional_cache_write(
        root / "symbol" / "day.json.z", b"cache", cache_root=root, reserve=0
    )
    assert native(root / ".optional_cache_bytes.json")["charged_bytes"] == 5


def test_joint_missing_reference_hash_survives_sorted_json_roundtrip():
    import json

    report = {"profiles": {code: {
        "decision": "holdout_pass_source_only_early_candidate",
        "candidate_revision": None,
    } for code in ("999999", "000001")}}
    inputs = portfolio.reference_inputs(report, "episode")
    restored = json.loads(json.dumps(report, sort_keys=True))
    assert inputs == portfolio.reference_inputs(restored, "episode")
    assert inputs["missing_reference_lanes"] == ["000001", "999999"]
    assert loop.digest(inputs) == loop.digest(portfolio.reference_inputs(restored, "episode"))
