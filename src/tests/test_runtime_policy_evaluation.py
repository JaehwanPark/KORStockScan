"""Latency optimizations retain dependency, consumer and snapshot contracts."""

import copy
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest
from src.engine.scalping import mechanistic_entry_runtime_policy as N
from src.engine.scalping import reversal_evaluation_context as E
from src.engine.infrastructure.snapshot_copy import snapshot_copy


@pytest.fixture
def loader(tmp_path, monkeypatch):
    N._CURRENT_CACHE.clear()
    N._CURRENT_FLIGHTS.clear()
    E._CONFIGURED = E._CONSUMED = None
    root = tmp_path / "data"
    root.mkdir()
    path = N.root(root) / "current.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"schema": "continuous_reversal_current_v6", "generation": 1})
    )
    calls = []

    def load(data_root, day):
        calls.append(1)
        pointer = N._read(path)
        return {
            "bundle_sha256": str(pointer["generation"]),
            "continuous_reversal": {
                "schema": "continuous_reversal_policy_v6",
                "release_commit": "commit",
                "cells": [{"value": 1}],
            },
        }

    monkeypatch.setattr(N, "_load_current_uncached", load)
    yield root, path, calls
    N._CURRENT_CACHE.clear()
    E._CONFIGURED = E._CONSUMED = None


def test_one_evaluation_is_immutable_and_next_boundary_revalidates(loader):
    root, path, calls = loader
    with (
        pytest.raises(ValueError, match="generation_changed"),
        N.verified_evaluation(data_root=root, target_date="2026-10-08") as view,
    ):
        assert N.load_effective(data_root=root, target_date="2026-10-08") is view
        with pytest.raises(TypeError):
            view["continuous_reversal"]["cells"][0]["value"] = 99
        with pytest.raises(TypeError):
            view["continuous_reversal"]["cells"].append({})
        owned = copy.deepcopy(view)
        owned["continuous_reversal"]["cells"][0]["value"] = 3
        assert view["continuous_reversal"]["cells"][0]["value"] == 1
        path.write_text(
            json.dumps({"schema": "continuous_reversal_current_v6", "generation": 2})
        )
        with pytest.raises(ValueError, match="generation_changed"):
            N.load_effective(data_root=root, target_date="2026-10-08")
    assert (
        N.load_effective(data_root=root, target_date="2026-10-08")["bundle_sha256"]
        == "2"
    )
    assert len(calls) == 2


@pytest.mark.parametrize("damage", [None, "source_changed", "invalid_source"])
def test_assessment_reuses_only_loader_validated_immutable_family(
    loader, monkeypatch, damage
):
    from src.engine.scalping import continuous_reversal_policy_v6 as V

    root, path, calls = loader
    original = N._load_current_uncached

    def load(*args):
        bundle = original(*args)
        bundle["continuous_reversal"]["family_sha256"] = "a" * 64
        return bundle

    monkeypatch.setattr(N, "_load_current_uncached", load)
    active = N.load_effective(data_root=root, target_date="2026-10-08", _immutable=True)
    family = active["continuous_reversal"]
    monkeypatch.setattr(V, "validate_family", lambda f: pytest.fail("repeated static validation"))
    if damage:
        path.write_text(path.read_text().replace('"generation": 1', '"generation": 2'))
        if damage == "invalid_source":
            monkeypatch.setattr(N, "_load_current_uncached", lambda *a: (_ for _ in ()).throw(ValueError("invalid_source")))
        with pytest.raises(ValueError, match="family_generation_changed|invalid_source"):
            V.assess(family, None, symbol="005930", session="krx_regular")
    else:
        result = V.assess(family, None, symbol="005930", session="krx_regular")
        assert result[0]["action"] == "BLOCK" and result[0]["family_sha256"] == "a" * 64
        assert len(calls) == 1
    assert N._VERIFIED_EVALUATION.get() is None
    assert N._SIGNATURE_PASS.get() is None


@pytest.mark.parametrize("kind", ["mutable", "forged", "evicted"])
def test_unissued_family_keeps_full_structural_validation(loader, monkeypatch, kind):
    from src.engine.scalping import continuous_reversal_policy_v6 as V

    root, path, calls = loader
    family = N.load_effective(data_root=root, target_date="2026-10-08", _immutable=True)["continuous_reversal"]
    if kind == "mutable":
        family = dict(family)
    elif kind == "forged":
        family = N._freeze(dict(family))
    else:
        N._CURRENT_CACHE.clear()
    def reject(f):
        assert f is family
        raise ValueError("structural_failure")
    monkeypatch.setattr(V, "validate_family", reject)
    with pytest.raises(ValueError, match="structural_failure"):
        V.assess(family, None, symbol="005930", session="krx_regular")


def test_verified_copy_preserves_ownership_aliases_cycles_and_unknown_protocol():
    class Custom:
        def __deepcopy__(self, memo):
            result = Custom()
            memo[id(self)] = result
            return result

    child = N._FrozenList([1, "scalar", {"nested": [None, True, 1.25]}])
    custom = Custom()
    source = N._FrozenDict({"first": child, "alias": child, "custom": custom})
    # Construct the cycle through the base method, like deepcopy's own memo
    # protocol; ordinary verified consumers cannot mutate either container.
    list.append(child, source)
    owned = copy.deepcopy(source)
    assert type(owned) is dict and type(owned["first"]) is list
    assert owned["first"] is owned["alias"]
    assert owned["first"][-1] is owned
    assert owned["custom"] is not custom
    owned["first"][2]["nested"].append("owned")
    assert child[2]["nested"] == [None, True, 1.25]
    with pytest.raises(TypeError):
        source["other"] = 1


def test_verified_copy_uses_scalar_fast_path_without_losing_full_policy(
    loader, monkeypatch
):
    root, path, calls = loader
    N.load_effective(data_root=root, target_date="2026-10-08")
    original = copy.deepcopy
    dispatched = []

    def checked(value, memo=None):
        dispatched.append(type(value))
        return original(value, memo)

    monkeypatch.setattr(copy, "deepcopy", checked)
    first = N.load_effective(data_root=root, target_date="2026-10-08")
    first["continuous_reversal"]["cells"][0]["value"] = 99
    second = N.load_effective(data_root=root, target_date="2026-10-08")
    assert second["continuous_reversal"]["cells"] == [{"value": 1}]
    assert set(dispatched) == {N._FrozenDict}
    assert len(calls) == 1


def test_same_mtime_size_and_atomic_replacement_invalidate(loader):
    root, path, calls = loader
    N.load_effective(data_root=root, target_date="2026-10-08")
    old = path.stat()
    path.write_text(path.read_text().replace(": 1", ": 2"))
    os.utime(path, ns=(old.st_atime_ns, old.st_mtime_ns))
    assert (
        N.load_effective(data_root=root, target_date="2026-10-08")["bundle_sha256"]
        == "2"
    )
    replacement = path.with_suffix(".next")
    replacement.write_bytes(path.read_bytes())
    os.utime(replacement, ns=(old.st_atime_ns, old.st_mtime_ns))
    replacement.replace(path)
    N.load_effective(data_root=root, target_date="2026-10-08")
    assert len(calls) == 3
    path.unlink()
    assert not N.dependencies_unchanged(next(iter(N._CURRENT_CACHE.values()))[0])


def test_symlink_replacement_even_same_target_invalidates(tmp_path):
    folder = tmp_path / "folder"
    folder.mkdir()
    (folder / "a").write_text("x")
    link = tmp_path / "link"
    link.symlink_to(folder, target_is_directory=True)
    before = N._signature(link / "a")
    link.unlink()
    link.symlink_to(folder, target_is_directory=True)
    assert N._signature(link / "a") != before
    with pytest.raises(ValueError, match="path_changed"):
        with N.signature_pass():
            N._signature(link / "a")
            link.unlink()
            link.symlink_to(folder, target_is_directory=True)


@pytest.mark.parametrize("linked", [False, True])
def test_signature_uses_one_fresh_leaf_metadata_read_per_check(
    tmp_path, monkeypatch, linked
):
    source = tmp_path / "source"
    source.write_text("original")
    path = tmp_path / "link" if linked else source
    if linked:
        path.symlink_to(source)
    real_stat, real_lstat = os.stat, os.lstat
    calls = []

    def stat(path, *args, **kwargs):
        if os.fspath(path) == str(source):
            calls.append("stat")
        return real_stat(path, *args, **kwargs)

    def lstat(path, *args, **kwargs):
        if os.fspath(path) == str(source):
            calls.append("lstat")
        return real_lstat(path, *args, **kwargs)

    monkeypatch.setattr(os, "stat", stat)
    monkeypatch.setattr(os, "lstat", lstat)
    with N.signature_pass():
        before = N._signature(str(path))
        assert before[2] == real_stat(source).st_ino
        assert calls == ["lstat"]
        source.write_text("modified")
        calls.clear()
        assert N._signature(str(path)) != before
        assert calls == ["lstat"]


@pytest.mark.parametrize("spelling", ["absolute", "relative", "symlink", "dot_parent"])
def test_signature_string_fast_path_preserves_path_and_mutation_checks(
    tmp_path, monkeypatch, spelling
):
    folder = tmp_path / "folder"
    folder.mkdir()
    source = folder / "source"
    source.write_text("original")
    link = tmp_path / "link"
    link.symlink_to(folder, target_is_directory=True)
    monkeypatch.chdir(tmp_path)
    path = {
        "absolute": str(source),
        "relative": "folder/source",
        "symlink": str(link / "source"),
        "dot_parent": str(folder) + "/../folder/source",
    }[spelling]
    with N.signature_pass():
        before = N._signature(path)
        assert before == N._signature(Path(path))
    original = source.stat()
    source.write_text("modified")
    os.utime(source, ns=(original.st_atime_ns, original.st_mtime_ns))
    assert N._signature(path) != before
    assert not N.dependencies_unchanged({path: before})


def test_concurrent_miss_single_flight_and_failure_does_not_reuse(loader, monkeypatch):
    root, path, calls = loader
    original = N._load_current_uncached
    entered = threading.Event()
    release = threading.Event()

    def slow(*args):
        entered.set()
        assert release.wait(1)
        return original(*args)

    monkeypatch.setattr(N, "_load_current_uncached", slow)
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [
            pool.submit(N.load_effective, data_root=root, target_date="2026-10-08")
            for _ in range(6)
        ]
        assert entered.wait(1)
        release.set()
        assert [f.result()["bundle_sha256"] for f in futures] == ["1"] * 6
    assert len(calls) == 1
    path.write_text(path.read_text().replace(": 1", ": 2"))
    monkeypatch.setattr(
        N,
        "_load_current_uncached",
        lambda *a: (_ for _ in ()).throw(ValueError("broken")),
    )
    with pytest.raises(ValueError, match="broken"):
        N.load_effective(data_root=root, target_date="2026-10-08")
    assert not N._CURRENT_FLIGHTS and not N._CURRENT_CACHE


def test_prepare_reuses_configuration_and_receipt_but_observes_overlay(
    loader, monkeypatch
):
    from src.engine.automation import intraday_release_handoff as H
    from src.engine.infrastructure import runtime_release_router as router
    from src.engine.scalping import (
        reversal_current_backend as D,
        reversal_auxiliary_intraday as I,
    )

    root, path, calls = loader
    configured = []
    receipts = []
    monkeypatch.setattr(router, "selected_release", lambda w: (root.parent, "commit"))
    monkeypatch.setattr(
        H,
        "_identity",
        lambda p: dict(pid=p, start_ticks="1", cwd=str(root.parent / "src")),
    )
    monkeypatch.setattr(
        H, "_paths", lambda day, commit: (root / "handoff", root / "consumed")
    )
    # The fixture configure callback owns this backend generation too; a
    # previous test's real backend must not force three reconfigurations.
    monkeypatch.setattr(D, "backend", lambda: SimpleNamespace(_GENERATION=None))
    monkeypatch.setattr(
        D, "configure_bundle", lambda bundle, **kw: configured.append(bundle)
    )

    def receipt(data_root, bundle):
        assert N.load_effective(data_root=data_root, target_date="2026-10-08") is bundle
        receipts.append(bundle)

    monkeypatch.setattr(I, "record_pid_consumption", receipt)
    for _ in range(3):
        E.prepare(data_root=root, day="2026-10-08")
    assert len(calls) == len(configured) == len(receipts) == 1
    overlay = I.root(root) / "current.json"
    overlay.parent.mkdir(parents=True)
    overlay.write_text("{}")
    E.prepare(data_root=root, day="2026-10-08")
    assert len(configured) == 1 and len(receipts) == 2
    E._CONFIGURED = None

    def fail(*a, **kw):
        raise ValueError("configure failed")

    monkeypatch.setattr(D, "configure_bundle", fail)
    with pytest.raises(ValueError, match="configure failed"):
        E.prepare(data_root=root, day="2026-10-08")
    assert E._CONFIGURED is None


def test_snapshot_copy_full_history_alias_cycles_and_consumer_isolation():
    from collections import deque

    rows = deque(
        [{"price": i, "nested": {"values": [i]}} for i in range(2000)], maxlen=2000
    )
    source = {"rows": rows, "alias": rows}
    source["cycle"] = source
    actual = snapshot_copy(source)
    assert actual["cycle"] is actual and actual["rows"] is actual["alias"]
    assert len(actual["rows"]) == 2000 and actual["rows"].maxlen == 2000
    actual["rows"][0]["nested"]["values"][0] = -1
    assert source["rows"][0]["nested"]["values"][0] == 0
    assert snapshot_copy(source)["rows"][0]["nested"]["values"][0] == 0


def test_actual_clock_is_acquired_after_claim_lock(monkeypatch):
    from src.engine.scalping import (
        reversal_source_diagnostics as S,
        reversal_current_backend as D,
    )

    now = [4.999]
    observed = []

    class Lock:
        def __enter__(self):
            now[0] = 5.001

        def __exit__(self, *a):
            pass

    backend = SimpleNamespace(
        _LOCK=Lock(), claim_snapshot=lambda **kw: observed.append(kw["now"])
    )
    monkeypatch.setattr(D, "backend", lambda: backend)
    monkeypatch.setattr(S.time, "time", lambda: now[0])
    S.claim_snapshot_with_receipt(now=4.999, live_clock=True)
    assert observed == [5.001]


def test_changed_during_validation_is_not_cached(loader, monkeypatch):
    root, path, calls = loader
    original = N._load_current_uncached

    def changed(*args):
        value = original(*args)
        path.write_text(path.read_text().replace(": 1", ": 2"))
        return value

    monkeypatch.setattr(N, "_load_current_uncached", changed)
    with pytest.raises(ValueError, match="dependency_changed"):
        N.load_effective(data_root=root, target_date="2026-10-08")
    assert not N._CURRENT_CACHE and not N._CURRENT_FLIGHTS


def test_validation_wait_is_bounded_and_never_returns_stale(loader):
    root, path, calls = loader
    N._CURRENT_FLIGHTS[N._current_cache_key(root, "2026-10-08")] = threading.Event()
    try:
        with pytest.raises(ValueError, match="validation_in_progress"):
            N.load_effective(data_root=root, target_date="2026-10-08")
    finally:
        N._CURRENT_FLIGHTS.clear()


def test_waiting_on_guard_cannot_resurrect_five_second_signal(monkeypatch):
    from src.engine.scalping import (
        reversal_source_diagnostics as S,
        reversal_current_backend as D,
    )

    now = [4.999]

    class Lock:
        def __enter__(self):
            now[0] = 5.001

        def __exit__(self, *a):
            pass

    def guard(claim, family, *, now):
        if now > 5:
            raise ValueError("reversal_signal_expired")
        return "valid"

    backend = SimpleNamespace(_LOCK=Lock(), validate_claim=guard, _CLAIMS={})
    monkeypatch.setattr(D, "backend", lambda *a: backend)
    monkeypatch.setattr(S.time, "time", lambda: now[0])
    monkeypatch.setattr(
        S, "_claim_failure_receipt", lambda *a: {"runtime_effect": False}
    )
    with pytest.raises(ValueError, match="expired"):
        S.validate_claim_with_receipt({}, "family", now=4.999, live_clock=True)


def test_performance_observes_every_loop_and_keeps_null_for_no_provider():
    from src.engine.monitoring import runtime_performance as P

    P.observe("loop_work", 0.1, generation="test-performance-only")
    for i in range(4200):
        P.observe("loop_work", i / 1000)
    s = P.snapshot()
    assert s["metrics"]["loop_work"]["total_observed"] == 4201
    assert s["metrics"]["loop_work"]["n"] == 4096
    assert s["metrics"]["provider_response"]["p99_seconds"] is None
    assert s["decision_authority"] == "none"


def test_absolute_symlink_dotdot_signature_matches_os_open(tmp_path):
    actual = tmp_path / "actual"
    actual.mkdir()
    (actual / "child").mkdir()
    (actual / "value").write_text("actual")
    (tmp_path / "value").write_text("other")
    link = tmp_path / "link"
    link.symlink_to(actual / "child", target_is_directory=True)
    source = link / ".." / "value"
    signature = N._signature(source)
    assert signature[0] == str(source.resolve())
    assert (
        N._source_hash(str(source), signature)
        == __import__("hashlib").sha256(b"actual").hexdigest()
    )


def test_launch_relative_mount_and_absolute_anchor_do_not_conflate(loader, monkeypatch):
    root, path, calls = loader
    launch = root.parent / "src"
    launch.mkdir()
    (launch / "data").symlink_to(root, target_is_directory=True)

    def load(data_root, day):
        calls.append(1)
        receipt = N._read(N.root(data_root) / "current.json")
        return {"bundle_sha256": str(receipt["generation"])}

    monkeypatch.setattr(N, "_load_current_uncached", load)
    monkeypatch.chdir(launch)
    N.load_effective(data_root=Path("data"), target_date="2026-10-08")
    with N.verified_evaluation(data_root=root, target_date="2026-10-08") as value:
        assert value["bundle_sha256"] == "1"
    with N.verified_evaluation(
        data_root=Path("data"), target_date="2026-10-08"
    ) as value:
        assert value["bundle_sha256"] == "1"
    assert len(calls) == 2


def test_full_ws_snapshot_and_signal_projection_equal_legacy_copy(monkeypatch):
    from collections import deque
    from src.engine import kiwoom_websocket as W
    from src.engine.infrastructure import snapshot_copy as C
    from src.engine.sniper_condition_handlers import build_tick_data_from_ws

    manager = W.KiwoomWSManager("offline")
    target = manager._ensure_target_defaults("005930")
    target.update(
        curr=1000,
        v_pw=130,
        price_history=deque(range(500), maxlen=500),
        strength_momentum_history=deque(
            [{"ts": 1.0, "price": 1000, "v_pw": 130, "nested": [1]}] * 2000
        ),
        recent_trade_ticks_by_route={
            "KRX|krx": deque([{"price": 1000, "qty": 3, "values": {"10": "1000"}}])
        },
    )
    monkeypatch.setattr(W.time, "time", lambda: 1234.0)
    fast = C.snapshot_copy
    monkeypatch.setattr(C, "snapshot_copy", copy.deepcopy)
    expected = manager.get_all_data(["005930"])
    monkeypatch.setattr(C, "snapshot_copy", fast)
    actual = manager.get_all_data(["005930"])
    assert actual == expected
    assert build_tick_data_from_ws(actual["005930"]) == build_tick_data_from_ws(
        expected["005930"]
    )
    actual["005930"]["strength_momentum_history"][0]["nested"][0] = -1
    assert target["strength_momentum_history"][0]["nested"] == [1]


def test_ws_concurrent_capture_keeps_epoch_item_and_nested_rows_coherent():
    from collections import deque
    from src.engine.kiwoom_websocket import KiwoomWSManager

    manager = KiwoomWSManager("offline")
    target = manager._ensure_target_defaults("005930")

    def produce():
        for i in range(1, 1000):
            with manager.lock:
                manager._market_data_transport_epoch = i
                target.update(
                    curr=i,
                    last_ws_item=str(i),
                    recent_trade_ticks=deque([{"price": i, "nested": [i]}]),
                )

    with ThreadPoolExecutor(max_workers=2) as pool:
        future = pool.submit(produce)
        for _ in range(80):
            value = manager.get_latest_data("005930")
            if value["curr"]:
                assert (
                    value["curr"]
                    == value["recent_trade_ticks"][0]["price"]
                    == value["market_data_transport_epoch"]
                )
                assert str(value["curr"]) == value["last_ws_item"]
        future.result()


def test_digest_cache_reuses_physical_file_but_detects_alias_and_content_changes(
    tmp_path,
):
    N._cached_source_hash.cache_clear()
    path = tmp_path / "source"
    path.write_bytes(b"one")
    alias = tmp_path / "alias"
    os.link(path, alias)
    first = N._source_hash(str(path), N._signature(path))
    assert N._source_hash(str(alias), N._signature(alias)) == first
    assert N._cached_source_hash.cache_info().misses == 1
    before = path.stat()
    path.write_bytes(b"two")
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    assert N._source_hash(str(alias), N._signature(alias)) != first
    expected = N._signature(alias)
    alias.unlink()
    alias.symlink_to(path)
    with pytest.raises(ValueError, match="changed_during_read"):
        N._source_hash(str(alias), expected)


@pytest.mark.parametrize("large_source_threshold", [0, 1024 * 1024])
def test_digest_cache_entry_and_byte_bounds_and_singleflight(
    tmp_path, monkeypatch, large_source_threshold
):
    N._cached_source_hash.cache_clear()
    monkeypatch.setattr(N, "_HASH_MAX_ENTRIES", 4)
    monkeypatch.setattr(N, "_HASH_MAX_BYTES", 2000)
    monkeypatch.setattr(N, "_HASH_LARGE_SOURCE_BYTES", large_source_threshold)
    for i in range(8):
        p = tmp_path / str(i)
        p.write_bytes(str(i).encode())
        N._source_hash(str(p), N._signature(p))
    assert N._cached_source_hash.cache_info().currsize <= 4 and N._HASH_BYTES <= 2000
    N._cached_source_hash.cache_clear()
    p = tmp_path / "parallel"
    p.write_bytes(b"parallel")
    sig = N._signature(p)
    original = N.hashlib.file_digest
    entered = threading.Event()
    release = threading.Event()
    reads = []

    def digest(*a):
        reads.append(1)
        entered.set()
        assert release.wait(1)
        return original(*a)

    monkeypatch.setattr(N.hashlib, "file_digest", digest)
    with ThreadPoolExecutor(max_workers=5) as pool:
        fs = [pool.submit(N._source_hash, str(p), sig) for _ in range(5)]
        assert entered.wait(1)
        release.set()
        assert len({f.result() for f in fs}) == 1
    assert len(reads) == 1 and not N._HASH_FLIGHTS
    N._cached_source_hash.cache_clear()


@pytest.mark.parametrize("mutate", [False, True])
def test_small_source_churn_does_not_rehash_unchanged_large_source(
    tmp_path, monkeypatch, mutate
):
    N._cached_source_hash.cache_clear()
    monkeypatch.setattr(N, "_HASH_MAX_ENTRIES", 4)
    monkeypatch.setattr(N, "_HASH_MAX_BYTES", 2800)
    monkeypatch.setattr(N, "_HASH_LARGE_SOURCE_BYTES", 16)
    large = tmp_path / "frozen"
    large.write_bytes(b"a" * 65536)
    original = N.hashlib.file_digest
    reads = []

    def measured(stream, *args):
        reads.append((stream.name, os.fstat(stream.fileno()).st_size))
        return original(stream, *args)

    monkeypatch.setattr(N.hashlib, "file_digest", measured)
    expected = N._source_hash(str(large), N._signature(large))
    for index in range(12):
        small = tmp_path / f"code-{index}"
        small.write_bytes(b"code")
        N._source_hash(str(small), N._signature(small))
    if mutate:
        before = large.stat()
        large.write_bytes(b"b" * 65536)
        os.utime(large, ns=(before.st_atime_ns, before.st_mtime_ns))
    current = N._source_hash(str(large), N._signature(large))
    assert (current != expected) == mutate
    assert sum(name == str(large) for name, size in reads) == 1 + int(mutate)
    assert sum(size for name, size in reads) == 65536 * (1 + int(mutate)) + 12 * 4
    assert len(N._HASH_CACHE) <= 4 and N._HASH_BYTES <= 2800
    N._cached_source_hash.cache_clear()


def test_digest_failure_or_concurrent_write_never_populates_cache(
    tmp_path, monkeypatch
):
    N._cached_source_hash.cache_clear()
    p = tmp_path / "source"
    p.write_bytes(b"original")
    sig = N._signature(p)
    original = N.hashlib.file_digest

    def broken(*args):
        raise OSError("read failed")

    monkeypatch.setattr(N.hashlib, "file_digest", broken)
    with pytest.raises(OSError, match="read failed"):
        N._source_hash(str(p), sig)
    assert not N._HASH_CACHE and not N._HASH_FLIGHTS

    def changed(*args):
        value = original(*args)
        p.write_bytes(b"modified")
        return value

    monkeypatch.setattr(N.hashlib, "file_digest", changed)
    with pytest.raises(ValueError, match="changed_during_read"):
        N._source_hash(str(p), sig)
    assert not N._HASH_CACHE and not N._HASH_FLIGHTS
    monkeypatch.setattr(N.hashlib, "file_digest", original)
    assert (
        N._source_hash(str(p), N._signature(p))
        == N.hashlib.sha256(b"modified").hexdigest()
    )
    N._cached_source_hash.cache_clear()


@pytest.fixture
def activation(tmp_path, monkeypatch):
    import fcntl
    from src.trading.order import owner_custody_registry as O

    monkeypatch.setenv(O.ACCOUNT_KEY_ENV, "test-account")
    registry = O.OrderOwnerRegistry(tmp_path / "registry.jsonl")
    args = dict(
        active_date="2026-10-08",
        policy_id="policy",
        symbol="005930",
        mode="COEXIST_ENTRY_ENABLED",
        allowed_owners=("main_scalping", "manual_operator"),
        migration_registry_tail_hash="1" * 64,
        broker_snapshot_sha256="2" * 64,
        entry_authority_hash="3" * 64,
    )
    event = dict(
        event="POLICY_ACTIVATED",
        state="POLICY_ACTIVE",
        account_key="test-account",
        order_date=args["active_date"],
        **{k: v for k, v in args.items() if k != "active_date"},
    )
    lock = registry._locked()
    try:
        row = registry._append_locked([], event)
    finally:
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        lock.close()
    args["activation_event_hash"] = row["event_hash"]
    return registry, args, O


def test_activation_row_reuse_still_checks_each_authority_field_and_account(
    activation, monkeypatch
):
    registry, args, O = activation
    read = registry._read_locked
    calls = []

    def counted():
        calls.append(1)
        return read()

    monkeypatch.setattr(registry, "_read_locked", counted)
    assert registry.policy_activation_matches(**args)
    for key, value in [
        ("active_date", "2026-10-07"),
        ("policy_id", "other"),
        ("symbol", "000660"),
        ("mode", "COEXIST_EXIT_ONLY"),
        ("allowed_owners", ("manual_operator",)),
        ("migration_registry_tail_hash", "4" * 64),
        ("broker_snapshot_sha256", "5" * 64),
        ("entry_authority_hash", "6" * 64),
    ]:
        assert not registry.policy_activation_matches(**dict(args, **{key: value}))
    monkeypatch.setenv(O.ACCOUNT_KEY_ENV, "different-account")
    assert not registry.policy_activation_matches(**args)
    assert len(calls) == 1


@pytest.mark.parametrize(
    "mutation", ["same_size_mtime", "replace", "symlink", "missing", "append"]
)
def test_activation_row_cache_observes_journal_mutation(activation, mutation):
    import fcntl

    registry, args, O = activation
    p = registry.path
    assert registry.policy_activation_matches(**args)
    old = p.stat()
    if mutation == "same_size_mtime":
        p.write_text(p.read_text().replace("test-account", "evil-account"))
        os.utime(p, ns=(old.st_atime_ns, old.st_mtime_ns))
    elif mutation in {"replace", "symlink"}:
        other = p.with_name("other")
        other.write_text("{}\n")
        if mutation == "replace":
            other.replace(p)
        else:
            p.unlink()
            p.symlink_to(other)
    elif mutation == "missing":
        p.unlink()
        assert not registry.policy_activation_matches(**args)
        return
    else:
        lock = registry._locked()
        try:
            registry._append_locked(registry._read_locked(), {"event": "TEST_APPEND"})
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()
        old_signature = registry._activation_signature
        assert registry.policy_activation_matches(**args)
        assert registry._activation_signature != old_signature
        return
    with pytest.raises(O.OwnerRegistryConflict):
        registry.policy_activation_matches(**args)
    assert not registry._activation_rows


def test_activation_row_cache_bounds_and_concurrent_reads(activation, monkeypatch):
    registry, args, O = activation
    read = registry._read_locked
    calls = []

    def counted():
        calls.append(1)
        return read()

    monkeypatch.setattr(registry, "_read_locked", counted)
    with ThreadPoolExecutor(max_workers=5) as pool:
        assert all(
            pool.map(lambda _: registry.policy_activation_matches(**args), range(20))
        )
    assert len(calls) == 1
    for i in range(70):
        assert not registry.policy_activation_matches(
            **dict(args, activation_event_hash=f"{i:064x}")
        )
    assert len(registry._activation_rows) <= 64
    assert all(v is None or len(v) <= 4096 for v in registry._activation_rows.values())


def test_activation_row_during_read_change_fails_and_cache_rows_are_isolated(
    activation, monkeypatch
):
    import fcntl

    registry, args, O = activation
    read = registry._read_locked

    def changed():
        rows = read()
        registry.path.write_text(registry.path.read_text() + "\n")
        return rows

    monkeypatch.setattr(registry, "_read_locked", changed)
    with pytest.raises(O.OwnerRegistryConflict, match="changed_during_activation_read"):
        registry.policy_activation_matches(**args)
    assert not registry._activation_rows
    monkeypatch.setattr(registry, "_read_locked", read)
    assert registry.policy_activation_matches(**args)
    lock = registry._locked()
    try:
        row = registry._activation_row_locked(args["activation_event_hash"])
        row["allowed_owners"].clear()
    finally:
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        lock.close()
    assert registry.policy_activation_matches(**args)


def test_activation_oversize_row_uses_verified_uncached_read(activation, monkeypatch):
    import fcntl

    registry, args, O = activation
    lock = registry._locked()
    try:
        events = registry._read_locked()
        event = dict(events[0])
        event.pop("event_hash")
        event.pop("previous_hash")
        event["padding"] = "x" * 5000
        row = registry._append_locked(events, event)
    finally:
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        lock.close()
    args["activation_event_hash"] = row["event_hash"]
    read = registry._read_locked
    calls = []

    def counted():
        calls.append(1)
        return read()

    monkeypatch.setattr(registry, "_read_locked", counted)
    assert registry.policy_activation_matches(**args)
    assert registry.policy_activation_matches(**args)
    assert (
        len(calls) == 2
        and args["activation_event_hash"] not in registry._activation_rows
    )


@pytest.mark.parametrize(
    "damage", [None, "native_invalid", "source_changed", "backend_changed"]
)
def test_post_response_prepared_claim_rechecks_source_and_native_eligibility(
    loader, monkeypatch, damage
):
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import (
        reversal_current_backend as D,
        reversal_extended_union as A,
        reversal_source_diagnostics as DIAG,
    )
    from src.utils import constants

    root, pointer, _ = loader
    family = dict(
        schema=V.SCHEMA,
        release_commit="commit",
        family_sha256="family",
        machine_cells={
            "cell": {
                "routes": {
                    "SOR": {"scope_execution_hash": "scope", "backend": "union_v6"}
                }
            }
        },
    )

    def load(*args):
        N._read(pointer)  # Retain the loader's actual pointer dependency.
        return {"bundle_sha256": "bundle", "continuous_reversal": family}

    monkeypatch.setattr(N, "_load_current_uncached", load)
    seen = []
    backend = SimpleNamespace(_GENERATION="family")
    monkeypatch.setattr(D, "backend", lambda: backend)

    def validate(claim, generation, *, now):
        seen.append((claim, generation, now))
        if damage == "native_invalid":
            raise ValueError("reversal_signal_path_changed")
        return ({"branch_signals": {"legacy_dd5_ge_0_4_v1": {}}}, {})

    monkeypatch.setattr(D, "validate_any_claim", validate)
    monkeypatch.setattr(
        DIAG, "validate_claim_with_receipt",
        lambda claim, generation, *, now, **kw: validate(claim, generation, now=now),
    )
    monkeypatch.setattr(
        V,
        "validate_family",
        lambda *a: pytest.fail("static family was already verified"),
    )
    monkeypatch.setattr(E.time, "time", lambda: 10.0)
    monkeypatch.setattr(constants, "DATA_DIR", root)
    now = (
        __import__("datetime")
        .datetime.fromisoformat("2026-10-08T12:00:00+09:00")
        .timestamp()
    )
    ref = "legacy_dd5_ge_0_4_v1:" + A.definition_hash("legacy_dd5_ge_0_4_v1")
    policy = {
        "continuous_reversal_claim": {"token": "original"},
        "continuous_reversal_assessment": {
            "cell_key": "cell",
            "route": "SOR",
            "scope_execution_hash": "scope",
            "matched_policy_refs": [ref],
        },
    }
    with N.verified_evaluation(data_root=root, target_date="2026-10-08") as active:
        E._CONFIGURED = E._CONSUMED = (("same-pid-consumer",), active)

        def prepare(**kw):
            assert kw == {"data_root": root, "day": "2026-10-08"}
            if damage == "source_changed":
                return {}
            if damage == "backend_changed":
                backend._GENERATION = "other"
            return active

        monkeypatch.setattr(E, "prepare", prepare)
        if damage:
            with pytest.raises(
                ValueError, match="path_changed|scope_execution_changed"
            ):
                V.validate_active_claim(policy, active, now=now)
        else:
            assert V.validate_active_claim(policy, active, now=now) == [ref]
            assert seen == [({"token": "original"}, "family", 10.0)]


@pytest.mark.parametrize("mutation", [False, True])
def test_engine_post_response_boundary_preserves_wait_and_rejects_source_race(
    loader, monkeypatch, mutation
):
    from src.tests.test_ai_engine_openai_transport import _build_engine
    from src.engine.scalping import continuous_reversal_policy as P
    from src.utils import constants

    root, path, _ = loader
    monkeypatch.setattr(constants, "DATA_DIR", root)
    day = (
        __import__("datetime")
        .datetime.now(__import__("zoneinfo").ZoneInfo("Asia/Seoul"))
        .date()
        .isoformat()
    )
    policy = dict(
        continuous_reversal_assessment={
            "policy_version": "continuous_reversal_policy_v6",
            "action": "ENTER_NOW",
        },
        machine_bundle_sha256="bundle",
    )

    def compose(response, issued):
        assert N._VERIFIED_EVALUATION.get()[:2] == (str(root), day)
        if mutation:
            path.write_text(path.read_text().replace(": 1", ": 2"))
        return dict(action="WAIT", entry_ai_screen_pass=False)

    monkeypatch.setattr(P, "compose", compose)
    result = _build_engine()._normalize_decision_quality_entry_result(
        {"risk_verdict": "PASS"}, exact_payload={}, live_policy=policy
    )
    assert result["action"] == "WAIT" and result["entry_ai_screen_pass"] is False
    if mutation:
        assert result["reason"] == "entry_post_response_source_invalid"
        assert result["entry_machine_pass_submit_candidate"] is False
    assert N._VERIFIED_EVALUATION.get() is None
