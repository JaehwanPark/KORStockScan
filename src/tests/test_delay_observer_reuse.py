"""Native observer reuse must invalidate without weakening startup verification."""

import os
from concurrent.futures import ThreadPoolExecutor

import pytest

from src.engine.automation import runtime_policy_bootstrap as bootstrap
from src.engine.scalping import pre_submit_delay_initial_policy as initial
from src.tests.test_pre_submit_delay_initial_policy import build


@pytest.fixture
def policy_generation(tmp_path, monkeypatch):
    report, policy = build(tmp_path, monkeypatch, [{"prices": {0: 10000, 30: 10000}}])
    initial.publish(tmp_path, report, policy, expected_incumbent=None)
    monkeypatch.setattr(bootstrap, "DATA_DIR", tmp_path)
    monkeypatch.setattr(bootstrap, "_DELAY_OBSERVER_CACHE", {})
    monkeypatch.setattr(bootstrap, "_DELAY_OBSERVER_METRICS", {})
    return tmp_path


def test_native_success_reuse_isolated_values_and_full_default(
    policy_generation, monkeypatch
):
    calls = []
    original = initial.validate

    def validate(*a, **kw):
        calls.append(1)
        return original(*a, **kw)

    monkeypatch.setattr(initial, "validate", validate)
    expected = bootstrap._pre_submit_delay_handoff("2026-10-05")
    calls.clear()
    for _ in range(5):
        actual = bootstrap._pre_submit_delay_handoff("2026-10-05", observer_reuse=True)
        assert actual == expected
        actual[1]["status"] = "caller_mutation"
    assert len(calls) == 1
    assert bootstrap._DELAY_OBSERVER_METRICS["mode"] == "reuse"
    bootstrap._pre_submit_delay_handoff("2026-10-05")
    assert len(calls) > 1


@pytest.mark.parametrize(
    "damage", ["same_size", "replace", "delete", "new_partition", "date"]
)
def test_changes_do_not_reuse_success(policy_generation, damage):
    first = bootstrap._pre_submit_delay_handoff("2026-10-05", observer_reuse=True)
    assert first[1]["status"] == "verified_initial_timing_policy"
    source = next(
        (policy_generation / "threshold_cycle").glob(
            "date=*/family=pre_submit_delay/part-execution-*.jsonl"
        )
    )
    before = source.stat()
    if damage == "same_size":
        raw = source.read_bytes()
        source.write_bytes(raw.replace(b"10000", b"10001", 1))
        os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
    elif damage == "replace":
        other = source.with_suffix(".swap")
        other.write_bytes(source.read_bytes())
        other.replace(source)
    elif damage == "delete":
        source.unlink()
    elif damage == "new_partition":
        source.with_name("part-execution-late.jsonl").write_text("{}\n")
    result = bootstrap._pre_submit_delay_handoff(
        "2026-10-06" if damage == "date" else "2026-10-05", observer_reuse=True
    )
    assert bootstrap._DELAY_OBSERVER_METRICS["mode"] == "full"
    if damage in {"same_size", "delete", "new_partition"}:
        assert result[1]["status"] == "invalid_committed_generation"


def test_source_changes_during_native_validation_are_rejected(
    policy_generation, monkeypatch
):
    original = initial.verify_source

    mutations = []

    def mutate(*args, **kwargs):
        assert kwargs == {"pipeline_reference_only": True}
        original(*args, **kwargs)
        path = next(
            (policy_generation / "threshold_cycle").glob(
                "date=*/family=pre_submit_delay/part-execution-*.jsonl"
            )
        )
        path.write_bytes(path.read_bytes() + b"\n")
        mutations.append(path)

    monkeypatch.setattr(initial, "verify_source", mutate)
    result = bootstrap._pre_submit_delay_handoff("2026-10-05", observer_reuse=True)
    assert result[1]["status"] == "invalid_committed_generation"
    assert len(mutations) == 1
    assert bootstrap._DELAY_OBSERVER_CACHE["entry"]["error"] == (
        "observer_delay_validation_failed:ValueError"
    )
    assert "value" not in bootstrap._DELAY_OBSERVER_CACHE["entry"]


def test_concurrent_observers_share_one_validation(policy_generation, monkeypatch):
    calls = []
    original = initial.validate

    def validate(*a, **kw):
        calls.append(1)
        return original(*a, **kw)

    monkeypatch.setattr(initial, "validate", validate)
    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(
            pool.map(
                lambda _: bootstrap._pre_submit_delay_handoff(
                    "2026-10-05", observer_reuse=True
                ),
                range(3),
            )
        )
    assert all(x[1]["status"] == "verified_initial_timing_policy" for x in rows)
    assert len(calls) == 1


def test_observer_mode_cannot_write_or_prepare():
    with pytest.raises(ValueError, match="read_only"):
        bootstrap.verify_bootstrap("2026-10-05", observer_reuse=True)
    with pytest.raises(ValueError, match="read_only"):
        bootstrap.verify_bootstrap(
            "2026-10-05",
            observer_reuse=True,
            write=False,
            output_dir=bootstrap.DATA_DIR,
        )


def test_noncanonical_native_tree_is_not_cache_eligible(tmp_path):
    ref = {"path": "nested/leaf.json", "sha256": "a" * 64, "size": 10, "count": 1}
    assert not bootstrap._observer_canonical_tree_layout(tmp_path, {"tree": ref}, {})
    ref["path"] = "shards/" + "a" * 64 + ".json"
    assert bootstrap._observer_canonical_tree_layout(tmp_path, {"tree": ref}, {})


def test_failed_generation_backoff_and_repair(policy_generation, monkeypatch):
    original = initial.verify_source
    calls = []

    def fail(*a, **kw):
        assert kw == {"pipeline_reference_only": True}
        calls.append(1)
        raise ValueError("source_unavailable")

    monkeypatch.setattr(initial, "verify_source", fail)
    for _ in range(2):
        result = bootstrap._pre_submit_delay_handoff("2026-10-05", observer_reuse=True)
        assert result[1]["status"] == "invalid_committed_generation"
    assert len(calls) == 1
    assert bootstrap._DELAY_OBSERVER_CACHE["entry"]["error"] == (
        "observer_delay_validation_failed:ValueError"
    )
    bootstrap._DELAY_OBSERVER_CACHE["entry"]["retry_after"] = 0
    monkeypatch.setattr(initial, "verify_source", original)
    result = bootstrap._pre_submit_delay_handoff("2026-10-05", observer_reuse=True)
    assert result[1]["status"] == "verified_initial_timing_policy"
