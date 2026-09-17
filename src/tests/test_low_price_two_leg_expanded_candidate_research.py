from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta
import json
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from src.engine.monitoring import (
    low_price_two_leg_expanded_candidate_research as expanded,
)
from src.engine.monitoring.low_price_two_leg_entry_spot_research import (
    Bar,
    ResearchError,
    build_day_contexts,
    fetch_sor_history,
)
from src.trading.low_price_two_leg.profiles import PROFILES

LEGACY_TEST_RESEARCH_PROFILES = {
    **expanded.RESEARCH_PROFILES,
    **expanded._new_symbol_profiles({"017670": "SK텔레콤", "007660": "이수페타시스"}),
}


class FakeResponse:
    status_code = 200
    headers = {}

    def __init__(self, rows):
        self._rows = rows

    def json(self):
        return {"return_code": 0, "stk_min_pole_chart_qry": self._rows}


def test_expanded_research_fingerprint_is_stable_and_policy_sensitive(
    monkeypatch, tmp_path
) -> None:
    profile_id, profile = next(iter(expanded.RESEARCH_PROFILES.items()))
    bar = Bar(
        datetime(2026, 9, 14, 9, 10, tzinfo=ZoneInfo("Asia/Seoul")),
        1000,
        1010,
        990,
        1005,
    )
    kwargs = {
        "sources": {
            profile.symbol: (
                [bar],
                {
                    "source_quality_status": "PASS",
                    "source_content_sha256": "a" * 64,
                },
            )
        },
        "target_date": date(2026, 9, 14),
        "candidate_symbols": {profile.symbol: profile.name},
        "research_profiles": {profile_id: profile},
        "dynamic_universe_source_date": date(2026, 9, 14),
        "applied_policy_snapshots": {profile_id: {"policy_hash": "b" * 64}},
    }

    first = expanded.research_input_fingerprint(**kwargs)
    assert first == expanded.research_input_fingerprint(**kwargs)
    kwargs["applied_policy_snapshots"] = {profile_id: {"policy_hash": "c" * 64}}
    assert first != expanded.research_input_fingerprint(**kwargs)
    kwargs["applied_policy_snapshots"] = {profile_id: {"policy_hash": "b" * 64}}

    from pathlib import Path

    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "schema": expanded.REPORT_SCHEMA,
                "target_date": "2026-09-14",
                "status": "complete",
                "source_input_fingerprint": first,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        )
    )
    original_read = Path.read_bytes
    for helper_name in ("low_price_two_leg_entry_spot_research.py", "tick_utils.py"):
        with monkeypatch.context() as patch:
            patch.setattr(
                Path,
                "read_bytes",
                lambda path: original_read(path)
                + (b"\n# semantic revision\n" if path.name == helper_name else b""),
            )
            changed = expanded.research_input_fingerprint(**kwargs)
            assert changed != first
            assert (
                expanded.reusable_report(
                    report_path, target_date=kwargs["target_date"], fingerprint=changed
                )
                is None
            )
    with monkeypatch.context() as patch:
        original_contract = expanded.canonical_cost_contract()
        patch.setattr(
            expanded,
            "canonical_cost_contract",
            lambda: {**original_contract, "version": "changed"},
        )
        assert expanded.research_input_fingerprint(**kwargs) != first
    with monkeypatch.context() as patch:
        patch.setattr(expanded, "COST_PCT", expanded.COST_PCT + 0.01)
        assert expanded.research_input_fingerprint(**kwargs) != first
    assert expanded.research_input_fingerprint(**kwargs) == first


def test_exact_date_report_reuse_requires_matching_fingerprint(tmp_path) -> None:
    path = tmp_path / "report.json"
    report = _notification_report()
    report["source_input_fingerprint"] = "a" * 64
    report["result_cache_receipt"] = {
        "schema": expanded.REPORT_CACHE_SCHEMA,
        "body_sha256": expanded._report_cache_digest(report),
    }
    path.write_text(json.dumps(report), encoding="utf-8")

    assert (
        expanded.reusable_report(
            path, target_date=date(2026, 8, 24), fingerprint="a" * 64
        )
        == report
    )
    assert (
        expanded.reusable_report(
            path, target_date=date(2026, 8, 24), fingerprint="b" * 64
        )
        is None
    )


@pytest.mark.parametrize("raw", ["[]", "null", "1", '"text"', "{", '{"schema":null}'])
def test_reusable_report_corrupt_or_non_object_is_cache_miss(tmp_path, raw):
    path = tmp_path / "report.json"
    path.write_text(raw)
    assert (
        expanded.reusable_report(
            path, target_date=date(2026, 9, 14), fingerprint="a" * 64
        )
        is None
    )


def _sealed_cache_report():
    report = _notification_report()
    report["source_input_fingerprint"] = "a" * 64
    report["result_cache_receipt"] = {
        "schema": expanded.REPORT_CACHE_SCHEMA,
        "body_sha256": expanded._report_cache_digest(report),
    }
    return report


def _read_cache_fixture(path):
    return expanded.reusable_report(
        path, target_date=date(2026, 8, 24), fingerprint="a" * 64
    )


def test_report_writer_seals_current_body_without_mutating_caller(
    monkeypatch, tmp_path
):
    from copy import deepcopy

    report = _sealed_cache_report()
    report["telegram_status"] = "sent"
    before = deepcopy(report)
    monkeypatch.setattr(
        expanded, "render_markdown", lambda value: "source-only fixture\n"
    )
    path, _ = expanded.write_report(report, tmp_path)
    restored = _read_cache_fixture(path)
    assert restored is not None
    assert restored["telegram_status"] == "sent"
    assert (
        restored["result_cache_receipt"]["body_sha256"]
        != before["result_cache_receipt"]["body_sha256"]
    )
    assert report == before
    assert expanded.CandidateRecommendationNotifier._valid_report(restored)


@pytest.mark.parametrize(
    "key,value",
    [
        ("profiles", {}),
        ("recommendations", [{}]),
        ("cost_pct", 0),
        ("telegram_status", "forged"),
        ("source_meta", {}),
    ],
)
def test_report_cache_body_tamper_is_miss(tmp_path, key, value):
    report = _sealed_cache_report()
    report[key] = value
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report))
    assert _read_cache_fixture(path) is None


@pytest.mark.parametrize(
    "key,value",
    [
        ("status", "running"),
        ("status", "waiting"),
        ("status", "failed"),
        ("status", "source_quality_blocked"),
        ("status", "complete"),
        ("status", []),
        ("authority", "real_order_authority"),
        ("actual_order_submitted", True),
        ("cost_pct", 0),
        ("profiles", []),
        ("recommendations", [{}]),
    ],
)
def test_report_cache_seal_does_not_replace_semantic_validation(tmp_path, key, value):
    report = _sealed_cache_report()
    report[key] = value
    report["result_cache_receipt"]["body_sha256"] = expanded._report_cache_digest(
        report
    )
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report))
    assert _read_cache_fixture(path) is None


def test_old_unsealed_report_and_nonfinite_result_are_miss(tmp_path):
    report = _sealed_cache_report()
    path = tmp_path / "report.json"
    report.pop("result_cache_receipt")
    path.write_text(json.dumps(report))
    assert _read_cache_fixture(path) is None
    report = _sealed_cache_report()
    report["diagnostic"] = float("nan")
    path.write_text(json.dumps(report))
    assert _read_cache_fixture(path) is None


@pytest.mark.parametrize(
    "kind",
    ["leaf_symlink", "parent_symlink", "fifo", "oversize", "changed_during_read"],
)
def test_report_cache_rejects_unsafe_or_unstable_reader(monkeypatch, tmp_path, kind):
    import os
    import stat

    path = tmp_path / "report.json"
    path.write_text(json.dumps(_sealed_cache_report()))
    if kind == "leaf_symlink":
        other = tmp_path / "link.json"
        other.symlink_to(path)
        path = other
    elif kind == "parent_symlink":
        parent = tmp_path / "linked"
        parent.symlink_to(tmp_path, target_is_directory=True)
        path = parent / path.name
    elif kind == "fifo":
        path = tmp_path / "fifo"
        os.mkfifo(path)
    elif kind == "oversize":
        monkeypatch.setattr(expanded, "REPORT_CACHE_MAX_BYTES", 8)
    elif kind == "changed_during_read":
        original = os.fstat
        calls = 0

        def altered(fd):
            nonlocal calls
            value = original(fd)
            if stat.S_ISREG(value.st_mode):
                calls += 1
                if calls == 2:
                    return SimpleNamespace(
                        **{
                            key: getattr(value, key)
                            for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns")
                        },
                        st_ctime_ns=value.st_ctime_ns + 1,
                    )
            return value

        monkeypatch.setattr(expanded.os, "fstat", altered)
    assert _read_cache_fixture(path) is None


@pytest.mark.parametrize("notification", [None, "sent", "duplicate", "send_failed"])
def test_main_verified_reuse_preserves_notification_handoff(
    monkeypatch, tmp_path, notification
):
    report = _sealed_cache_report()
    path = tmp_path / f"{expanded.REPORT_TYPE}_2026-08-24.json"
    path.write_text(json.dumps(report))
    calls = []

    def forbidden(*args, **kwargs):
        raise AssertionError("verified reuse must not acquire or replay")

    monkeypatch.setattr(
        expanded.kiwoom_utils, "get_cached_kiwoom_token", lambda: "test"
    )
    monkeypatch.setattr(
        expanded, "_dynamic_candidate_snapshot", lambda *a, **k: (None, {})
    )
    monkeypatch.setattr(
        expanded,
        "load_applied_profile_policy",
        lambda *a, **k: (None, "", "unavailable"),
    )
    monkeypatch.setattr(
        expanded,
        "_load_source_cache",
        lambda **k: ([], {"source_quality_status": "PASS"}),
    )
    monkeypatch.setattr(
        expanded, "load_research_census", lambda *a, **k: None, raising=False
    )
    monkeypatch.setattr(expanded, "research_input_fingerprint", lambda **k: "a" * 64)
    monkeypatch.setattr(expanded, "fetch_sor_history", forbidden)
    monkeypatch.setattr(expanded, "build_report", forbidden)
    monkeypatch.setattr(expanded, "render_markdown", lambda value: "fixture\n")
    monkeypatch.setattr(
        expanded, "_attach_admission_evidence", lambda value, **k: value, raising=False
    )
    monkeypatch.setattr(
        expanded.CandidateRecommendationNotifier,
        "notify",
        lambda self, value: calls.append(value["target_date"]) or notification,
    )
    args = ["--target-date", "2026-08-24", "--output-dir", str(tmp_path), "--write"]
    if notification is not None:
        args.append("--notify")
    if notification == "send_failed":
        with pytest.raises(RuntimeError, match="telegram_not_delivered:send_failed"):
            expanded.main(args)
    else:
        assert expanded.main(args) == 0
    assert calls == ([] if notification is None else ["2026-08-24"])
    restored = _read_cache_fixture(path)
    assert restored is not None
    if notification is not None:
        assert restored["telegram_status"] == notification


def test_partial_source_quality_terminal_can_reuse_without_extra_economic_gate(
    tmp_path,
):
    report = _sealed_cache_report()
    report["status"] = "partial_source_quality"
    symbol = next(iter(report["source_meta"]))
    report["source_meta"].pop(symbol)
    report["source_quarantine"][symbol] = "isolated_source_gap"
    report["eligible_source_symbol_count"] -= 1
    report["quarantined_source_symbol_count"] += 1
    report["result_cache_receipt"]["body_sha256"] = expanded._report_cache_digest(
        report
    )
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report))
    assert _read_cache_fixture(path) == report


def test_interrupted_cache_publication_keeps_previous_verified_body(
    monkeypatch, tmp_path
):
    report = _sealed_cache_report()
    path = tmp_path / f"{expanded.REPORT_TYPE}_2026-08-24.json"
    path.write_text(json.dumps(report))
    before = path.read_bytes()
    report["telegram_status"] = "sent"
    monkeypatch.setattr(expanded, "render_markdown", lambda value: "fixture\n")

    def interrupted(*args, **kwargs):
        raise OSError("publication interrupted")

    monkeypatch.setattr(expanded.os, "replace", interrupted)
    with pytest.raises(OSError, match="publication interrupted"):
        expanded.write_report(report, tmp_path)
    assert path.read_bytes() == before
    assert _read_cache_fixture(path) is not None
    assert sorted(p.name for p in tmp_path.iterdir()) == [path.name]


def _selection_checkpoint_fixture(mode="zero"):
    profile = PROFILES["samsung_heavy_midday"]
    anchor = datetime.combine(
        date(2026, 6, 5), profile.policy.scan_start, tzinfo=ZoneInfo("Asia/Seoul")
    ) - timedelta(minutes=60)
    bars = [
        Bar(
            anchor + timedelta(days=day, minutes=index),
            20000,
            20000 if mode == "zero" or (mode == "held" and index >= 60) else 20600,
            20000,
            20000,
        )
        for day in range(46)
        for index in range(180)
    ]
    return profile, expanded.build_day_contexts(bars)


@pytest.mark.parametrize("mode", ["zero", "complete", "held"])
def test_profile_checkpoint_exact_replay_and_fresh_mutable_results(
    monkeypatch, tmp_path, mode
):
    from copy import deepcopy

    profile, contexts = _selection_checkpoint_fixture(mode)
    expected = expanded.select_profile_spot(profile, deepcopy(contexts))
    contract = {"input": "frozen", "cost": expanded.COST_PCT}
    stats = {}
    cold = expanded._select_profile_checkpoint(
        profile,
        deepcopy(contexts),
        calibration_days=30,
        cache_dir=tmp_path,
        contract=contract,
        stats=stats,
    )
    assert cold == expected
    assert stats == {"miss": 1}
    if mode == "held":
        assert cold["baseline"]["full"]["held_legs"] > 0
    if mode == "complete":
        assert cold["baseline"]["full"]["completed_legs"] > 0
    monkeypatch.setattr(
        expanded, "select_profile_spot", lambda *a, **k: pytest.fail("warm replay")
    )
    warm = expanded._select_profile_checkpoint(
        profile,
        deepcopy(contexts),
        calibration_days=30,
        cache_dir=tmp_path,
        contract=contract,
        stats=stats,
    )
    assert warm == expected
    assert stats == {"miss": 1, "hit": 1}
    warm["baseline"]["full"]["held_legs"] = 999
    again = expanded._select_profile_checkpoint(
        profile,
        deepcopy(contexts),
        calibration_days=30,
        cache_dir=tmp_path,
        contract=contract,
    )
    assert again == expected
    assert len(list(tmp_path.glob("*.json"))) == 1


@pytest.mark.parametrize(
    "kind",
    [
        "contract",
        "tamper",
        "nonfinite",
        "resealed_authority",
        "resealed_cost",
        "resealed_dates",
        "resealed_baseline",
        "corrupt",
        "symlink",
        "oversize",
    ],
)
def test_profile_checkpoint_invalid_cache_falls_back_to_original_selection(
    monkeypatch, tmp_path, kind
):
    profile, contexts = _selection_checkpoint_fixture()
    contract = {"input": "frozen"}
    expected = expanded._select_profile_checkpoint(
        profile, contexts, calibration_days=30, cache_dir=tmp_path, contract=contract
    )
    path = next(tmp_path.glob("*.json"))
    payload = json.loads(path.read_bytes())
    if kind == "contract":
        contract = {"input": "corrected"}
    elif kind in {
        "tamper",
        "nonfinite",
        "resealed_authority",
        "resealed_cost",
        "resealed_dates",
        "resealed_baseline",
    }:
        if kind == "tamper":
            payload["result"]["recommended_spot"] = {"target_ticks": 100}
        elif kind == "nonfinite":
            payload["result"]["diagnostic"] = float("nan")
        elif kind == "resealed_authority":
            payload["result"]["selected"]["full"]["actual_order_submitted"] = True
        elif kind == "resealed_cost":
            payload["result"]["selected"]["full"]["cost_pct"] = 0
        elif kind == "resealed_dates":
            payload["result"]["date_split"]["holdout_start"] = "2026-06-05"
        else:
            payload["result"]["baseline"]["parameters"]["target_ticks"] = 100
        if kind.startswith("resealed_"):
            payload["body_sha256"] = expanded._report_cache_digest(
                {k: v for k, v in payload.items() if k != "body_sha256"}
            )
        path.write_text(json.dumps(payload))
    elif kind == "corrupt":
        path.write_text("{")
    elif kind == "symlink":
        stored = tmp_path / "preserved"
        path.rename(stored)
        path.symlink_to(stored)
    elif kind == "oversize":
        monkeypatch.setattr(expanded, "PROFILE_CHECKPOINT_MAX_BYTES", 8)
    calls = []
    monkeypatch.setattr(
        expanded, "select_profile_spot", lambda *a, **k: calls.append(1) or expected
    )
    actual = expanded._select_profile_checkpoint(
        profile, contexts, calibration_days=30, cache_dir=tmp_path, contract=contract
    )
    assert actual == expected
    assert calls == [1]
    if kind == "symlink":
        assert path.is_symlink()


def test_profile_checkpoint_interrupted_write_is_optional_and_cleans_temp(
    monkeypatch, tmp_path
):
    profile, contexts = _selection_checkpoint_fixture()
    expected = expanded.select_profile_spot(profile, contexts)
    monkeypatch.setattr(
        expanded.os,
        "replace",
        lambda *a, **k: (_ for _ in ()).throw(OSError("interrupted")),
    )
    assert (
        expanded._select_profile_checkpoint(
            profile,
            contexts,
            calibration_days=30,
            cache_dir=tmp_path,
            contract={"input": "frozen"},
        )
        == expected
    )
    assert not list(tmp_path.glob("*.json"))
    assert not list(tmp_path.rglob(".selection-*"))
    assert not list(tmp_path.rglob(".day-cache-*"))
    assert not list(tmp_path.rglob(".cache-bytes-*"))


def test_report_profile_checkpoints_selectively_replay_corrected_symbol_and_keep_source_gate(
    monkeypatch, tmp_path
):
    from copy import deepcopy

    end = date(2026, 8, 10)
    dates = expanded.clean_baseline_trading_dates(end)
    profiles = {}
    for key, profile in expanded.RESEARCH_PROFILES.items():
        if profile.discovery_lane == "new_symbol" and profile.session == "morning":
            profiles[key] = profile
            if len(profiles) == 2:
                break
    assert len({p.symbol for p in profiles.values()}) == 2
    inventory = SimpleNamespace(
        research_profiles=profiles,
        candidate_symbols={p.symbol: p.name for p in profiles.values()},
        research_symbols={p.symbol for p in profiles.values()},
        live_profiles={},
        active_symbol_sessions=set(),
        implemented_symbols={},
        new_symbol_profiles=profiles,
        time_extension_profiles={},
        logic_improvement_profiles={},
    )
    monkeypatch.setattr(
        expanded, "_target_date_research_inventory", lambda *a, **k: inventory
    )
    monkeypatch.setattr(
        expanded, "_attach_admission_evidence", lambda value, **k: value, raising=False
    )
    sources = {}
    for profile in profiles.values():
        bars = []
        for day in dates:
            anchor = datetime.combine(
                day, profile.policy.scan_start, tzinfo=ZoneInfo("Asia/Seoul")
            ) - timedelta(minutes=60)
            bars.extend(
                Bar(anchor + timedelta(minutes=i), 20000, 20600, 20000, 20000)
                for i in range(180)
            )
        sources[profile.symbol] = (
            bars,
            {"source_quality_status": "PASS", "source_content_sha256": "a" * 64},
        )
    calls = []
    original = expanded.select_profile_spot
    monkeypatch.setattr(
        expanded,
        "select_profile_spot",
        lambda profile, *a, **k: calls.append(profile.symbol)
        or original(profile, *a, **k),
    )

    def build(values, cache):
        result = expanded.build_report(
            sources=values,
            start_date=expanded.CLEAN_BASELINE_DATE,
            end_date=end,
            checkpoint_cache_dir=cache,
        )
        result.pop("generated_at_kst")
        return result

    reference = build(deepcopy(sources), None)
    calls.clear()
    assert build(deepcopy(sources), tmp_path) == reference
    assert len(calls) == 2
    calls.clear()
    assert build(deepcopy(sources), tmp_path) == reference
    assert calls == []
    changed = deepcopy(sources)
    symbol = next(iter(changed))
    changed[symbol][0][-1] = replace(changed[symbol][0][-1], close_price=20100)
    # Unchanged external markers must not hide an actual bar correction.
    reference = build(deepcopy(changed), None)
    calls.clear()
    assert build(deepcopy(changed), tmp_path) == reference
    assert calls == [symbol]
    calls.clear()
    changed[symbol][1]["source_quality_status"] = "FAIL"
    result = build(changed, tmp_path)
    assert calls == []
    assert result["source_quarantine"][symbol] == "source_quality_not_pass"
    assert all(
        row["decision"] == "source_quality_quarantined_no_evaluation"
        for row in result["profiles"].values()
        if row["symbol"] == symbol
    )


def test_profile_checkpoint_parent_replacement_does_not_publish_to_new_parent(
    monkeypatch, tmp_path
):
    import os

    parent = tmp_path / "cache"
    path = parent / "result.json"
    original = os.stat
    moved = False

    def changed(value, *args, **kwargs):
        nonlocal moved
        if value == parent and not moved:
            moved = True
            parent.rename(tmp_path / "old")
            parent.mkdir()
        return original(value, *args, **kwargs)

    # mkdir itself may stat: arm the replacement only after temporary fd write.
    original_fsync = os.fsync

    def arm(fd):
        original_fsync(fd)
        monkeypatch.setattr(os, "stat", changed)

    monkeypatch.setattr(os, "fsync", arm)
    assert not expanded._write_profile_checkpoint(path, {"fixture": "no authority"})
    assert moved
    assert list(parent.iterdir()) == []
    assert list((tmp_path / "old").iterdir()) == []


def test_stable_cache_reader_requests_actual_size_not_memory_cap(monkeypatch, tmp_path):
    path = tmp_path / "small.json"
    path.write_text('{"fixture":true}')
    original = expanded.os.fdopen
    reads = []

    class SizedReader:
        def __init__(self, handle):
            self.handle = handle

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.handle.close()

        def fileno(self):
            return self.handle.fileno()

        def read(self, count):
            reads.append(count)
            return self.handle.read(count)

    monkeypatch.setattr(
        expanded.os, "fdopen", lambda *a, **k: SizedReader(original(*a, **k))
    )
    assert expanded._read_stable_json(path, max_bytes=1024 * 1024 * 1024) == {
        "fixture": True
    }
    assert reads == [path.stat().st_size + 1]


def test_expanded_profiles_separate_new_symbols_and_inactive_existing_sessions():
    assert len(expanded.NEW_SYMBOL_PROFILES) == (
        len(expanded.CANDIDATE_SYMBOLS) * len(expanded.SESSION_WINDOWS)
    )
    assert len(expanded.RESEARCH_PROFILES) == (
        len(expanded.NEW_SYMBOL_PROFILES)
        + len(expanded.EXISTING_SYMBOL_TIME_EXTENSION_PROFILES)
        + len(expanded.EXISTING_SYMBOL_LOGIC_IMPROVEMENT_PROFILES)
    )
    assert set(expanded.CANDIDATE_SYMBOLS).isdisjoint(
        profile.symbol for profile in PROFILES.values()
    )
    assert {
        (profile.symbol, profile.session)
        for profile in expanded.NEW_SYMBOL_PROFILES.values()
    } == {
        (symbol, session)
        for symbol in expanded.CANDIDATE_SYMBOLS
        for session in expanded.SESSION_WINDOWS
    }
    assert len(expanded.EXISTING_SYMBOL_TIME_EXTENSION_PROFILES) == (
        len(expanded.IMPLEMENTED_SYMBOLS) * len(expanded.SESSION_WINDOWS)
        - len(expanded.ACTIVE_SYMBOL_SESSIONS)
    )
    assert len(expanded.EXISTING_SYMBOL_LOGIC_IMPROVEMENT_PROFILES) == len(PROFILES)
    assert set(expanded.EXISTING_SYMBOL_LOGIC_IMPROVEMENT_PROFILES) == {
        f"logic_{profile_id}" for profile_id in PROFILES
    }
    existing_profile = expanded.EXISTING_SYMBOL_TIME_EXTENSION_PROFILES[
        "existing_006800_afternoon"
    ]
    assert existing_profile.discovery_lane == "existing_symbol_time_extension"
    assert (existing_profile.symbol, existing_profile.session) not in (
        expanded.ACTIVE_SYMBOL_SESSIONS
    )


def test_theborn_morning_is_fixed_source_only_operator_observation_candidate():
    profile = expanded.NEW_SYMBOL_PROFILES["candidate_475560_morning"]
    contract = expanded._operator_observation_contract(profile)

    assert expanded.CANDIDATE_SYMBOLS["475560"] == "더본코리아"
    assert profile.fixed_observation is True
    assert profile.policy.scan_start.strftime("%H:%M") == "09:40"
    assert profile.policy.scan_last_bar.strftime("%H:%M") == "09:59"
    assert profile.policy.lookback_bars == 20
    assert profile.policy.rolling_high_drawdown_pct == pytest.approx(0.50)
    assert profile.policy.rolling_low_proximity_pct == pytest.approx(0.35)
    assert profile.policy.entry_offsets_ticks == (0, -1)
    assert profile.policy.entry_valid_completed_bars == 5
    assert profile.policy.target_ticks == 4
    assert contract is not None
    assert contract["status"] == "source_only_keep_collecting"
    assert contract["runtime_effect"] is False
    assert contract["actual_order_submitted"] is False
    assert contract["broker_order_forbidden"] is True
    assert contract["metric_contract"] == {
        "metric_role": "fixed_episode_candidate_holdout_observation",
        "decision_authority": "source_only_observation_no_runtime_authority",
        "window_policy": (
            "clean_baseline_expanding_calibration_latest_16_trading_days_holdout"
        ),
        "sample_floor": {"signal_episodes": 3, "completed_legs": 4},
        "primary_decision_metric": "notional_weighted_ev_pct",
        "source_quality_gate": [
            "official_ka10080_success",
            "requested_start_date_fully_bracketed",
            "valid_unique_completed_sor_regular_ohlc",
            "fixed_policy_identity_match",
            "completed_legs_only_for_ev",
            "active_unrealized_separated_from_completed_ev",
        ],
        "missing_execution_evidence": [
            "prospective_fresh_bbo_spread",
            "passive_fill_feasibility",
            "spread_and_fee_adjusted_target_ev",
        ],
        "forbidden_uses": [
            "daily_policy_reoptimization",
            "automatic_machine_implementation_or_service_start",
            "automatic_runtime_or_preopen_policy_promotion",
            "minute_bar_holdout_pass_as_machine_recommendation_without_bbo_economics",
            "account_or_order_api",
            "real_order_submission",
            "provider_bot_cap_threshold_or_broker_guard_change",
            "stop_loss_or_forced_exit_creation",
            "thin_oos_or_diagnostic_win_rate_as_live_authority",
        ],
    }


def test_fixed_operator_observation_never_enters_implementation_recommendations():
    profile = expanded.NEW_SYMBOL_PROFILES["candidate_475560_morning"]
    profiles = {
        profile.profile_id: {
            "decision": "holdout_pass_source_only_early_candidate",
            "symbol": profile.symbol,
            "name": profile.name,
            "session": profile.session,
            "recommended_spot": expanded.baseline_candidate(profile).public(),
            "selected": {
                "holdout": {
                    "signal_episodes": 10,
                    "completed_legs": 20,
                    "held_legs": 0,
                    "held_leg_rate_per_filled_leg": 0.0,
                    "notional_weighted_ev_pct": 1.0,
                }
            },
            "baseline": {
                "holdout": {
                    "notional_weighted_ev_pct": 1.0,
                }
            },
        }
    }
    source_meta = {
        profile.symbol: {
            "latest_close_price": 30_000,
        }
    }

    assert (
        expanded._recommendation_rows(
            profiles,
            source_meta,
            research_profiles={profile.profile_id: profile},
        )
        == []
    )


def test_fetch_expanded_symbol_requires_explicit_research_allowlist():
    symbol = next(iter(expanded.CANDIDATE_SYMBOLS))
    started = date(2026, 6, 5)
    dates = [started + timedelta(days=index) for index in range(46)]
    rows = [
        {
            "cntr_tm": f"{item.strftime('%Y%m%d')}131500",
            "open_pric": "20000",
            "high_pric": "20100",
            "low_pric": "19900",
            "cur_prc": "20000",
        }
        for item in dates
    ]
    rows.append(
        {
            "cntr_tm": "20260604131500",
            "open_pric": "20000",
            "high_pric": "20100",
            "low_pric": "19900",
            "cur_prc": "20000",
        }
    )

    with pytest.raises(ValueError, match="symbol_not_in_selected_profile_allowlist"):
        fetch_sor_history(
            symbol=symbol,
            token="TOKEN",
            start_date=started,
            end_date=dates[-1],
            post=lambda *args, **kwargs: FakeResponse(rows),
        )

    bars, meta = fetch_sor_history(
        symbol=symbol,
        token="TOKEN",
        start_date=started,
        end_date=dates[-1],
        post=lambda *args, **kwargs: FakeResponse(rows),
        allowed_symbols=frozenset({symbol}),
    )
    assert len(bars) == 46
    assert meta["source_quality_status"] == "PASS"


def test_expanded_report_fails_closed_on_incomplete_source_universe():
    with pytest.raises(
        ResearchError, match="all_research_symbols_source_quality_blocked"
    ):
        expanded.build_report(
            sources={},
            start_date=expanded.CLEAN_BASELINE_DATE,
            end_date=date(2026, 8, 10),
        )


def test_expanded_report_rejects_target_date_profile_policy_drift():
    end_date = date(2026, 8, 21)
    inventory = expanded._target_date_research_inventory(end_date)
    research_profiles = dict(inventory.research_profiles)
    profile_id = sorted(research_profiles)[0]
    profile = research_profiles[profile_id]
    research_profiles[profile_id] = replace(
        profile,
        policy=replace(profile.policy, target_ticks=profile.policy.target_ticks + 1),
    )

    with pytest.raises(
        ResearchError, match="research_profile_target_date_inventory_mismatch"
    ):
        expanded.build_report(
            sources={},
            start_date=expanded.CLEAN_BASELINE_DATE,
            end_date=end_date,
            candidate_symbols=inventory.candidate_symbols,
            research_profiles=research_profiles,
        )


def test_expanded_report_builds_daily_artifact_for_complete_source_universe(
    monkeypatch,
):
    end_date = date(2026, 8, 11)
    target_inventory = expanded._target_date_research_inventory(end_date)
    start_date = expanded.CLEAN_BASELINE_DATE
    trading_dates = list(expanded.clean_baseline_trading_dates(end_date))
    monkeypatch.setattr(
        expanded,
        "build_day_contexts",
        lambda bars: {item: object() for item in trading_dates},
    )
    monkeypatch.setattr(
        expanded,
        "select_profile_spot",
        lambda profile, contexts, **kwargs: {
            "symbol": profile.symbol,
            "name": profile.name,
            "session": profile.session,
            "decision": "no_calibration_candidate",
            "recommended_spot": None,
            "baseline": {
                "holdout": {
                    "signal_episodes": 0,
                    "completed_legs": 0,
                    "held_legs": 0,
                    "notional_weighted_ev_pct": None,
                }
            },
        },
    )
    sources = {
        symbol: (
            [SimpleNamespace(close_price=20_000)],
            {"source_quality_status": "PASS"},
        )
        for symbol in target_inventory.research_symbols
    }

    report = expanded.build_report(
        sources=sources,
        start_date=start_date,
        end_date=end_date,
    )

    assert report["status"] == "no_qualified_candidate"
    assert len(report["profiles"]) == len(target_inventory.research_profiles)
    assert report["trading_date_count"] == 47
    assert report["calibration_trading_day_count"] == 31
    assert report["holdout_trading_day_count"] == 16
    assert report["existing_symbol_time_extension_profile_count"] == len(
        target_inventory.time_extension_profiles
    )
    assert report["existing_symbol_logic_improvement_profile_count"] == len(
        target_inventory.logic_improvement_profiles
    )
    assert report["recommendation_count"] == 0
    assert report["runtime_effect"] is False
    assert report["operator_observation_candidate_count"] == 1
    assert set(report["operator_observation_candidate_inventory"]) == {
        "candidate_475560_morning"
    }


def test_expanded_report_quarantines_one_bad_symbol_without_blocking_others(
    monkeypatch,
):
    end_date = date(2026, 8, 11)
    target_inventory = expanded._target_date_research_inventory(end_date)
    trading_dates = list(expanded.clean_baseline_trading_dates(end_date))
    monkeypatch.setattr(
        expanded,
        "build_day_contexts",
        lambda bars: {item: object() for item in trading_dates},
    )
    monkeypatch.setattr(
        expanded,
        "select_profile_spot",
        lambda profile, contexts, **kwargs: {
            "symbol": profile.symbol,
            "name": profile.name,
            "session": profile.session,
            "decision": "no_calibration_candidate",
            "recommended_spot": None,
            "baseline": {"holdout": {"notional_weighted_ev_pct": None}},
        },
    )
    missing_symbol = sorted(target_inventory.research_symbols)[0]
    sources = {
        symbol: (
            [SimpleNamespace(close_price=20_000)],
            {"source_quality_status": "PASS"},
        )
        for symbol in target_inventory.research_symbols
        if symbol != missing_symbol
    }

    report = expanded.build_report(
        sources=sources,
        start_date=expanded.CLEAN_BASELINE_DATE,
        end_date=end_date,
    )

    assert report["status"] == "partial_source_quality"
    assert report["source_quarantine"] == {missing_symbol: "source_missing"}
    assert (
        report["eligible_source_symbol_count"]
        == len(target_inventory.research_symbols) - 1
    )
    assert all(
        item["decision"] == "source_quality_quarantined_no_evaluation"
        for item in report["profiles"].values()
        if item["symbol"] == missing_symbol
    )


def test_daily_window_expands_from_clean_baseline_and_keeps_latest_16_holdout():
    dates_0810 = expanded.clean_baseline_trading_dates(date(2026, 8, 10))
    dates_0811 = expanded.clean_baseline_trading_dates(date(2026, 8, 11))

    assert len(dates_0810) == 46
    assert len(dates_0811) == 47
    assert dates_0810[0] == dates_0811[0] == date(2026, 6, 5)
    assert dates_0811[-1] == date(2026, 8, 11)
    assert len(dates_0811[: -expanded.HOLDOUT_DAYS]) == 31
    assert len(dates_0811[-expanded.HOLDOUT_DAYS :]) == 16
    with pytest.raises(ValueError, match="target_date_not_krx_trading_day"):
        expanded.clean_baseline_trading_dates(date(2026, 8, 9))


def test_dynamic_universe_adds_ranked_under_100000_symbols_only(tmp_path):
    path = tmp_path / "daily.csv"
    (tmp_path / expanded.DEFAULT_DYNAMIC_UNIVERSE_DIAGNOSTIC_PATH.name).write_text(
        '{"latest_date":"2026-08-11","selected_count":3}', encoding="utf-8"
    )
    path.write_text(
        "date,code,name,close,score_rank\n"
        "2026-08-11,000990,DB하이텍,93200,2\n"
        "2026-08-11,042700,고가종목,213000,1\n"
        "2026-08-11,017670,기존검토종목,86000,3\n",
        encoding="utf-8",
    )

    result = expanded._dynamic_candidate_symbols(date(2026, 8, 11), path=path)

    assert result == {"000990": "DB하이텍"}


def test_dynamic_universe_uses_latest_completed_snapshot_not_after_target(tmp_path):
    path = tmp_path / "daily.csv"
    diagnostic_path = tmp_path / "completion.json"
    diagnostic_path.write_text(
        '{"latest_date":"2026-08-11","selected_count":1}', encoding="utf-8"
    )
    path.write_text(
        "date,code,name,close,score_rank\n2026-08-11,000990,DB하이텍,93200,2\n",
        encoding="utf-8",
    )

    source_date, result = expanded._dynamic_candidate_snapshot(
        date(2026, 8, 12), path=path, diagnostic_path=diagnostic_path
    )

    assert source_date == date(2026, 8, 11)
    assert result == {"000990": "DB하이텍"}

    diagnostic_path.write_text(
        '{"latest_date":"2026-08-13","selected_count":1}', encoding="utf-8"
    )
    assert expanded._dynamic_candidate_snapshot(
        date(2026, 8, 12), path=path, diagnostic_path=diagnostic_path
    ) == (None, {})

    diagnostic_path.write_text(
        '{"latest_date":"2026-08-11","selected_count":2}', encoding="utf-8"
    )
    assert expanded._dynamic_candidate_snapshot(
        date(2026, 8, 12), path=path, diagnostic_path=diagnostic_path
    ) == (None, {})


def test_dynamic_universe_uses_target_date_implemented_symbol_inventory(tmp_path):
    target_date = date(2026, 8, 21)
    target_inventory = expanded._target_date_research_inventory(target_date)
    path = tmp_path / "daily.csv"
    diagnostic_path = tmp_path / "completion.json"
    diagnostic_path.write_text(
        '{"latest_date":"2026-08-21","selected_count":1}', encoding="utf-8"
    )
    path.write_text(
        "date,code,name,close,score_rank\n"
        "2026-08-21,111770,historical-dynamic-candidate,38600,1\n",
        encoding="utf-8",
    )

    assert "111770" in expanded.IMPLEMENTED_SYMBOLS
    assert "111770" not in target_inventory.implemented_symbols
    source_date, symbols = expanded._dynamic_candidate_snapshot(
        target_date,
        path=path,
        diagnostic_path=diagnostic_path,
        implemented_symbols=target_inventory.implemented_symbols,
    )

    assert source_date == target_date
    assert symbols == {"111770": "historical-dynamic-candidate"}


def test_dynamic_universe_report_pins_inventory_for_notifier_validation(monkeypatch):
    end_date = date(2026, 8, 21)
    trading_dates = list(expanded.clean_baseline_trading_dates(end_date))
    base_inventory = expanded._target_date_research_inventory(end_date)
    candidate_symbols = {
        **base_inventory.candidate_symbols,
        "000990": "DB하이텍",
    }
    target_inventory = expanded._target_date_research_inventory(
        end_date,
        candidate_symbols=candidate_symbols,
    )
    research_profiles = target_inventory.research_profiles
    source_symbols = target_inventory.research_symbols
    monkeypatch.setattr(
        expanded,
        "build_day_contexts",
        lambda bars: {item: object() for item in trading_dates},
    )
    monkeypatch.setattr(
        expanded,
        "select_profile_spot",
        lambda profile, contexts, **kwargs: {
            "symbol": profile.symbol,
            "name": profile.name,
            "session": profile.session,
            "decision": "no_calibration_candidate",
            "recommended_spot": None,
            "baseline": {"holdout": {"notional_weighted_ev_pct": None}},
        },
    )

    report = expanded.build_report(
        sources={
            symbol: (
                [SimpleNamespace(close_price=20_000)],
                {"source_quality_status": "PASS", "source_content_sha256": "a" * 64},
            )
            for symbol in source_symbols
        },
        start_date=expanded.CLEAN_BASELINE_DATE,
        end_date=end_date,
        candidate_symbols=candidate_symbols,
        research_profiles=research_profiles,
        dynamic_universe_source_date=end_date,
    )

    assert report["candidate_symbols"]["000990"] == "DB하이텍"
    assert report["dynamic_universe_source_date"] == "2026-08-21"
    assert report["new_symbol_profile_count"] == len(candidate_symbols) * len(
        expanded.SESSION_WINDOWS
    )
    assert report["existing_symbol_universe_size"] == 13
    assert report["existing_symbol_logic_improvement_profile_count"] == 27
    assert (
        len(expanded.LIVE_PROFILES)
        > report["existing_symbol_logic_improvement_profile_count"]
    )
    assert expanded.CandidateRecommendationNotifier._valid_report(report)

    report["dynamic_universe_source_date"] = "2026-08-24"
    assert not expanded.CandidateRecommendationNotifier._valid_report(report)
    report["dynamic_universe_source_date"] = None
    assert not expanded.CandidateRecommendationNotifier._valid_report(report)


def _profile_result(
    *,
    symbol: str,
    name: str,
    session: str,
    candidate_ev: float,
    baseline_ev: float,
    held_legs: int = 0,
    held_rate: float = 0.0,
    held_mark_pct: float | None = None,
) -> dict:
    return {
        "symbol": symbol,
        "name": name,
        "session": session,
        "baseline_policy_source": "target_date_applied_policy",
        "baseline_policy_hash": "test-applied-policy-hash",
        "decision": "holdout_pass_source_only_early_candidate",
        "recommended_spot": {
            "scan_start": "14:15",
            "scan_end": "14:24",
            "lookback_bars": 15,
            "rolling_high_drawdown_pct": 1.5,
            "rolling_low_proximity_pct": 0.2,
        },
        "selected": {
            "holdout": {
                "economic_replay_contract": expanded.ECONOMIC_REPLAY_CONTRACT,
                "observation_dates": [f"2026-08-{day:02d}" for day in range(1, 17)],
                "cost_pct": expanded.COST_PCT,
                "source_valid_observation_days": 16,
                "cost_adjusted_net_profit_krw_per_source_valid_observation_day": candidate_ev
                * 100,
                "signal_episodes": 4,
                "completed_legs": 7,
                "held_legs": held_legs,
                "held_leg_rate_per_filled_leg": held_rate,
                "active_unrealized_notional_weighted_pct": held_mark_pct,
                "worst_filled_max_adverse_excursion_pct": -0.5,
                "realized_net_profit_krw_per_episode": 100.0,
                "notional_weighted_ev_pct": candidate_ev,
            }
        },
        "baseline": {
            "holdout": {
                "notional_weighted_ev_pct": baseline_ev,
                "economic_replay_contract": expanded.ECONOMIC_REPLAY_CONTRACT,
                "observation_dates": [f"2026-08-{day:02d}" for day in range(1, 17)],
                "cost_pct": expanded.COST_PCT,
                "source_valid_observation_days": 16,
                "cost_adjusted_net_profit_krw_per_source_valid_observation_day": baseline_ev
                * 100,
            }
        },
    }


def test_recommendations_rank_profiles_and_enforce_daily_price_cap():
    profiles = {
        "existing_080220_afternoon": _profile_result(
            symbol="080220",
            name="제주반도체",
            session="afternoon",
            candidate_ev=0.08,
            baseline_ev=0.01,
        ),
        "candidate_017670_midday": _profile_result(
            symbol="017670",
            name="SK텔레콤",
            session="midday",
            candidate_ev=0.03,
            baseline_ev=0.01,
        ),
        "candidate_007660_afternoon": _profile_result(
            symbol="007660",
            name="이수페타시스",
            session="afternoon",
            candidate_ev=0.50,
            baseline_ev=0.01,
        ),
    }
    source_meta = {
        "080220": {"latest_close_price": 24_000},
        "017670": {"latest_close_price": 65_000},
        "007660": {"latest_close_price": 100_500},
    }

    rows = expanded._recommendation_rows(
        profiles,
        source_meta,
        research_profiles=LEGACY_TEST_RESEARCH_PROFILES,
    )

    assert [row["profile_id"] for row in rows] == [
        "existing_080220_afternoon",
        "candidate_017670_midday",
    ]
    assert rows[0]["price_band"] == "under_50000_krw"
    assert rows[1]["price_band"] == "50000_to_100000_krw"
    assert rows[0]["ev_uplift_pct_point"] == pytest.approx(0.07)
    assert all(row["runtime_effect"] is False for row in rows)


def test_recommendation_accepts_manageable_carry_and_rejects_excess_carry():
    manageable = _profile_result(
        symbol="017670",
        name="SK텔레콤",
        session="midday",
        candidate_ev=0.05,
        baseline_ev=0.01,
        held_legs=1,
        held_rate=0.20,
        held_mark_pct=-2.5,
    )
    excessive = _profile_result(
        symbol="007660",
        name="이수페타시스",
        session="midday",
        candidate_ev=0.20,
        baseline_ev=0.01,
        held_legs=1,
        held_rate=0.30,
        held_mark_pct=-2.5,
    )

    rows = expanded._recommendation_rows(
        {
            "candidate_017670_midday": manageable,
            "candidate_007660_midday": excessive,
        },
        {
            "017670": {"latest_close_price": 65_000},
            "007660": {"latest_close_price": 40_000},
        },
        research_profiles=LEGACY_TEST_RESEARCH_PROFILES,
    )

    assert [row["profile_id"] for row in rows] == ["candidate_017670_midday"]
    assert rows[0]["holdout_held_leg_rate_per_filled_leg"] == pytest.approx(0.20)


def test_target_date_logic_recommendation_requires_cumulative_candidate_and_rebound():
    kst = ZoneInfo("Asia/Seoul")
    target_date = date(2026, 8, 12)
    start = datetime(2026, 8, 12, 12, 52, tzinfo=kst)
    bars = [
        Bar(
            start + timedelta(minutes=index),
            22_000,
            22_100 if index < 30 else 22_000,
            21_950,
            21_950 if index >= 29 else 22_000,
        )
        for index in range(33)
    ]
    bars[31] = Bar(bars[31].timestamp, 21_950, 22_000, 21_950, 22_000)
    bars[32] = Bar(bars[32].timestamp, 22_000, 22_050, 21_950, 22_050)
    contexts = build_day_contexts(bars)
    profile_id = "logic_samsung_heavy_midday"
    profiles = {
        profile_id: {
            "decision": "holdout_pass_source_only_early_candidate",
            "recommended_spot": {
                "scan_start": "13:20",
                "scan_end": "13:29",
                "lookback_bars": 30,
                "rolling_high_drawdown_pct": 0.5,
                "rolling_low_proximity_pct": 0.35,
                "entry_offsets_ticks": [0, -1],
                "entry_valid_completed_bars": 5,
                "target_ticks": 2,
            },
        }
    }

    rows = expanded._target_date_logic_attribution(
        profiles=profiles,
        contexts_by_symbol={"010140": contexts},
        target_date=target_date,
        applied_policy_snapshots={
            "samsung_heavy_midday": {
                "status": "ready",
                "reason": "ready",
                "policy_hash": "test-policy-hash",
                "policy": {
                    "rolling_high_drawdown_pct": 0.75,
                    "rolling_low_proximity_pct": 0.35,
                    "lookback_bars": 30,
                    "entry_valid_completed_bars": 5,
                    "quantity": 2,
                    "target_ticks": 2,
                },
            }
        },
    )
    row = next(item for item in rows if item["profile_id"] == profile_id)

    assert row["decision"] == "recommend_cumulative_logic_candidate_review"
    assert row["applied_policy_status"] == "ready"
    assert row["applied_policy_hash"] == "test-policy-hash"
    assert row["baseline_target_date"]["signal_episodes"] == 0
    assert row["candidate_target_date"]["signal_episodes"] == 1
    assert row["candidate_target_date"]["completed_legs"] == 1
    assert row["candidate_target_date"]["no_fill_legs"] == 1
    assert row["candidate_target_date"]["held_legs"] == 0
    assert row["candidate_target_date"]["notional_weighted_ev_pct"] > 0

    unavailable_rows = expanded._target_date_logic_attribution(
        profiles=profiles,
        contexts_by_symbol={"010140": contexts},
        target_date=target_date,
        applied_policy_snapshots={},
    )
    unavailable = next(
        item for item in unavailable_rows if item["profile_id"] == profile_id
    )
    assert unavailable["decision"] == "not_recommended"
    assert unavailable["reason"] == "target_date_applied_policy_unavailable"


def test_logic_research_inventory_uses_target_date_applied_policy_as_baseline():
    snapshots = {
        "samsung_heavy_midday": {
            "status": "ready",
            "reason": "ready",
            "policy_hash": "applied-hash",
            "policy": {
                "rolling_high_drawdown_pct": 1.0,
                "rolling_low_proximity_pct": 0.25,
                "lookback_bars": 30,
                "entry_valid_completed_bars": 5,
                "quantity": 2,
                "target_ticks": 2,
            },
        }
    }

    _, profiles = expanded._research_inventory(
        expanded.CANDIDATE_SYMBOLS,
        applied_policy_snapshots=snapshots,
    )
    policy = profiles["logic_samsung_heavy_midday"].policy

    assert policy.rolling_high_drawdown_pct == 1.0
    assert policy.rolling_low_proximity_pct == 0.25


def test_existing_symbol_time_extension_recommendation_preserves_active_profile_lineage():
    profiles = {
        "existing_006800_afternoon": _profile_result(
            symbol="006800",
            name="미래에셋증권",
            session="afternoon",
            candidate_ev=0.08,
            baseline_ev=0.01,
        )
    }

    rows = expanded._recommendation_rows(
        profiles, {"006800": {"latest_close_price": 25_000}}
    )

    assert len(rows) == 1
    assert rows[0]["discovery_lane"] == "existing_symbol_time_extension"
    assert rows[0]["active_profile_ids_for_symbol"] == sorted(
        profile_id
        for profile_id, profile in PROFILES.items()
        if profile.symbol == "006800"
    )
    assert (rows[0]["symbol"], rows[0]["session"]) not in (
        expanded.ACTIVE_SYMBOL_SESSIONS
    )


def _notification_report(recommendations: list[dict] | None = None) -> dict:
    target_date = date(2026, 8, 24)
    target_inventory = expanded._target_date_research_inventory(target_date)
    rows = recommendations or []
    new_rows = [row for row in rows if row.get("discovery_lane") == "new_symbol"]
    existing_rows = [
        row
        for row in rows
        if row.get("discovery_lane") == "existing_symbol_time_extension"
    ]
    logic_rows = [
        row
        for row in rows
        if row.get("discovery_lane") == "existing_symbol_logic_improvement"
    ]
    attribution_rows = [
        {
            "profile_id": profile_id,
            "active_profile_id": profile_id.removeprefix("logic_"),
            "symbol": profile.symbol,
            "name": profile.name,
            "session": profile.session,
            "decision": "not_recommended",
            "reason": "cumulative_holdout_candidate_unavailable",
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
        for profile_id, profile in (target_inventory.logic_improvement_profiles.items())
    ]
    return {
        "schema": expanded.REPORT_SCHEMA,
        "report_type": expanded.REPORT_TYPE,
        "status": "recommendations_ready" if rows else "no_qualified_candidate",
        "authority": expanded.AUTHORITY,
        "target_date": target_date.isoformat(),
        "clean_tuning_baseline_date": "2026-06-05",
        "start_date": "2026-06-05",
        "end_date": "2026-08-24",
        "trading_date_count": 55,
        "calibration_trading_day_count": 39,
        "holdout_trading_day_count": 16,
        "cost_pct": expanded.COST_PCT,
        "cost_contract": expanded.canonical_cost_contract(),
        "candidate_universe_size": len(target_inventory.candidate_symbols),
        "candidate_symbols": target_inventory.candidate_symbols,
        "existing_symbol_universe_size": len(target_inventory.implemented_symbols),
        "source_symbol_count": len(target_inventory.research_symbols),
        "new_symbol_profile_count": len(target_inventory.new_symbol_profiles),
        "existing_symbol_time_extension_profile_count": len(
            target_inventory.time_extension_profiles
        ),
        "existing_symbol_logic_improvement_profile_count": len(
            target_inventory.logic_improvement_profiles
        ),
        "eligible_source_symbol_count": len(target_inventory.research_symbols),
        "quarantined_source_symbol_count": 0,
        "source_quarantine": {},
        "source_meta": {
            symbol: {"source_content_sha256": "a" * 64}
            for symbol in target_inventory.research_symbols
        },
        "research_profile_inventory": {
            profile_id: {
                "symbol": profile.symbol,
                "name": profile.name,
                "session": profile.session,
                "discovery_lane": profile.discovery_lane,
                "fixed_observation": profile.fixed_observation,
            }
            for profile_id, profile in target_inventory.research_profiles.items()
        },
        "operator_observation_candidate_count": len(
            expanded._operator_observation_inventory(target_inventory.research_profiles)
        ),
        "operator_observation_candidate_inventory": (
            expanded._operator_observation_inventory(target_inventory.research_profiles)
        ),
        "profiles": {
            profile_id: {
                "baseline_policy_source": "compiled_profile_baseline_not_recommendable",
                "existing_axis_economic_replay": {
                    "status": "source_runtime_policy_unavailable",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                },
                "observation_candidate": expanded._operator_observation_inventory(
                    target_inventory.research_profiles
                ).get(profile_id),
            }
            for profile_id in target_inventory.research_profiles
        },
        "recommendation_count": len(rows),
        "recommendations": rows,
        "new_symbol_recommendations": new_rows,
        "new_symbol_recommendation_count": len(new_rows),
        "existing_symbol_time_extension_recommendations": existing_rows,
        "existing_symbol_time_extension_recommendation_count": len(existing_rows),
        "existing_symbol_logic_improvement_recommendations": logic_rows,
        "existing_symbol_logic_improvement_recommendation_count": len(logic_rows),
        "target_date_logic_attribution": attribution_rows,
        "target_date_logic_attribution_count": len(attribution_rows),
        "postclose_logic_recommendations": [],
        "postclose_logic_recommendation_count": 0,
        "metric_contract": expanded.METRIC_CONTRACT,
        "recommendation_only": True,
        "machine_created": False,
        "service_started": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def test_admin_notifier_retries_sends_once_and_never_creates_machine(tmp_path):
    attempts = []
    sleeps = []

    def sender(token, admin_id, message):
        attempts.append((token, admin_id, message))
        if len(attempts) < 3:
            raise OSError("temporary telegram failure")

    notifier = expanded.CandidateRecommendationNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("token", "admin"),
        sender=sender,
        enabled=True,
        max_attempts=3,
        retry_delay_sec=0.5,
        sleeper=sleeps.append,
    )
    report = _notification_report()

    assert notifier.notify(report) == "sent"
    assert notifier.notify(report) == "duplicate"
    assert len(attempts) == 3
    assert sleeps == [0.5, 0.5]
    assert "자동 기계 구현·기동·실주문 권한 없음" in attempts[-1][2]
    state = (tmp_path / "state.json").read_text(encoding="utf-8")
    assert '"machine_created": false' in state
    assert '"service_started": false' in state


def test_new_report_rejects_legacy_cost_even_on_archive_date():
    report = _notification_report()
    assert expanded.CandidateRecommendationNotifier._valid_report(report)
    report["cost_pct"] = 0.20
    assert not expanded.CandidateRecommendationNotifier._valid_report(report)


def test_notifier_recomputes_paired_comparison_before_accepting_recommendation():
    inventory = expanded._target_date_research_inventory(date(2026, 8, 24))
    profile = next(
        item
        for item in inventory.new_symbol_profiles.values()
        if not item.fixed_observation
    )
    source = _profile_result(
        symbol=profile.symbol,
        name=profile.name,
        session=profile.session,
        candidate_ev=0.2,
        baseline_ev=0.1,
    )
    rows = expanded._recommendation_rows(
        {profile.profile_id: source},
        {profile.symbol: {"latest_close_price": 20000}},
        research_profiles=inventory.research_profiles,
        live_profiles=inventory.live_profiles,
        active_symbol_sessions=inventory.active_symbol_sessions,
    )
    assert len(rows) == 1
    report = _notification_report(rows)
    assert expanded.CandidateRecommendationNotifier._valid_report(report)
    rows[0]["candidate_economic_outcome"][
        "cost_adjusted_net_profit_krw_per_source_valid_observation_day"
    ] = 0
    assert not expanded.CandidateRecommendationNotifier._valid_report(report)


def test_telegram_message_separates_new_symbol_and_existing_time_extension_lanes():
    rows = expanded._recommendation_rows(
        {
            "candidate_017670_midday": _profile_result(
                symbol="017670",
                name="SK텔레콤",
                session="midday",
                candidate_ev=0.08,
                baseline_ev=0.01,
            ),
            "existing_006800_afternoon": _profile_result(
                symbol="006800",
                name="미래에셋증권",
                session="afternoon",
                candidate_ev=0.07,
                baseline_ev=0.01,
            ),
        },
        {
            "017670": {"latest_close_price": 65_000},
            "006800": {"latest_close_price": 25_000},
        },
        research_profiles=LEGACY_TEST_RESEARCH_PROFILES,
    )

    message = expanded.build_telegram_message(_notification_report(rows))

    assert "[신규 종목]" in message
    assert "[기존 종목·신규 시간대]" in message
    assert "SK텔레콤(017670)" in message
    assert "미래에셋증권(006800)" in message


def test_admin_notifier_fails_closed_for_invalid_authority(tmp_path):
    report = _notification_report()
    report["runtime_effect"] = True
    notifier = expanded.CandidateRecommendationNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("token", "admin"),
        sender=lambda *args: pytest.fail("invalid report must not be sent"),
        enabled=True,
    )

    assert notifier.notify(report) == "invalid_report"

    report = _notification_report()
    report["status"] = "recommendations_ready"
    assert notifier.notify(report) == "invalid_report"

    report = _notification_report()
    report["start_date"] = "2026-06-08"
    assert notifier.notify(report) == "invalid_report"

    report = _notification_report()
    report["operator_observation_candidate_inventory"]["candidate_475560_morning"][
        "policy"
    ]["target_ticks"] = 2
    assert notifier.notify(report) == "invalid_report"


def test_admin_notifier_exposes_exhausted_delivery_retries(tmp_path):
    attempts = []

    def sender(*args):
        attempts.append(args)
        raise OSError("telegram unavailable")

    notifier = expanded.CandidateRecommendationNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("token", "admin"),
        sender=sender,
        enabled=True,
        max_attempts=3,
        retry_delay_sec=0,
        sleeper=lambda _: None,
    )

    assert notifier.notify(_notification_report()) == "send_failed"
    assert len(attempts) == 3
    assert not (tmp_path / "state.json").exists()


def test_content_bound_source_cache_reuses_exact_bars_and_rejects_tamper(tmp_path):
    target_date = date(2026, 9, 4)
    bars = [
        Bar(
            datetime(2026, 9, 4, 13, 15, tzinfo=ZoneInfo("Asia/Seoul")),
            20_000,
            20_100,
            19_900,
            20_000,
        )
    ]
    meta = {
        "source_quality_status": "PASS",
        "bar_count": 1,
        "trading_date_count": 1,
    }
    path = expanded._write_source_cache(
        cache_dir=tmp_path,
        symbol="010140",
        start_date=target_date,
        end_date=target_date,
        expected_trading_day_count=1,
        bars=bars,
        meta=meta,
    )

    loaded = expanded._load_source_cache(
        cache_dir=tmp_path,
        symbol="010140",
        start_date=target_date,
        end_date=target_date,
        expected_trading_day_count=1,
    )
    assert loaded is not None
    assert loaded[0] == bars
    assert len(loaded[1]["source_content_sha256"]) == 64

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["bars"][0]["close_price"] = 19_900
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert (
        expanded._load_source_cache(
            cache_dir=tmp_path,
            symbol="010140",
            start_date=target_date,
            end_date=target_date,
            expected_trading_day_count=1,
        )
        is None
    )


def test_default_target_date_never_uses_an_incomplete_regular_session():
    assert expanded._default_target_date(
        now=expanded.datetime(2026, 8, 11, 14, 0, tzinfo=expanded.KST)
    ) == date(2026, 8, 10)
    assert expanded._default_target_date(
        now=expanded.datetime(2026, 8, 11, 20, 10, tzinfo=expanded.KST)
    ) == date(2026, 8, 11)


def test_source_quality_blocked_result_is_reported_to_admin_without_recommendation(
    tmp_path,
):
    report = expanded.build_source_quality_blocked_report(
        start_date=date(2026, 6, 5),
        end_date=date(2026, 8, 11),
        reason="015760_source_quality_fail",
    )
    report["telegram_status"] = "not_requested"
    sent = []
    notifier = expanded.CandidateRecommendationNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("token", "admin"),
        sender=lambda token, admin, message: sent.append(message),
        enabled=True,
    )

    assert report["status"] == "source_quality_blocked"
    assert report["recommendations"] == []
    assert notifier.notify(report) == "sent"
    assert "source-quality 문제로 신규 추천을 산출하지 않았습니다" in sent[0]
    assert "015760_source_quality_fail" in sent[0]
    assert "관찰 입력 차단(source-quality)" in sent[0]
    assert "OOS 0/3" not in sent[0]


def test_telegram_transport_requires_explicit_ok_response(monkeypatch):
    class TelegramResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"ok": false, "description": "chat not found"}'

    monkeypatch.setattr(
        expanded.request, "urlopen", lambda request, timeout: TelegramResponse()
    )

    with pytest.raises(RuntimeError, match="telegram_send_not_ok"):
        expanded._send_telegram("token", "admin", "message")


def test_malformed_postclose_logic_recommendation_is_rejected_without_error():
    assert not expanded._valid_postclose_logic_recommendation(
        {
            "applied_policy_status": "ready",
            "applied_policy_reason": "ready",
            "applied_policy_hash": "hash",
            "baseline_target_date": {},
            "candidate_target_date": {"notional_weighted_ev_pct": None},
        }
    )


def test_daily_network_failure_becomes_source_quality_admin_artifact(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        expanded.kiwoom_utils, "get_cached_kiwoom_token", lambda: "TOKEN"
    )

    def fail_fetch(**kwargs):
        raise expanded.requests.ConnectionError("network unavailable")

    monkeypatch.setattr(expanded, "fetch_sor_history", fail_fetch)

    assert (
        expanded.main(
            [
                "--target-date",
                "2026-08-11",
                "--output-dir",
                str(tmp_path),
                "--write",
            ]
        )
        == 0
    )
    report = expanded.json.loads(
        (
            tmp_path / "low_price_two_leg_expanded_candidate_research_2026-08-11.json"
        ).read_text(encoding="utf-8")
    )
    assert report["status"] == "source_quality_blocked"
    assert report["telegram_status"] == "not_requested"
    assert "network unavailable" in report["source_quality_reasons"][0]
