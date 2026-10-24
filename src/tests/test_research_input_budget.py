"""Resident ownership copies cannot mint bytes or release another owner."""

from concurrent.futures import ThreadPoolExecutor
from copy import copy, deepcopy
import gc
import hashlib
from pathlib import Path
import pickle
from threading import Barrier

import pytest

from src.engine.lifecycle import research_input_budget as budget
from src.engine.scalping.initial_quantity_source_cache import (
    BoundedRows,
    ResidentFacts,
    ResidentPaths,
)


@pytest.fixture
def initial():
    gc.collect()
    before = budget.health()["used_bytes"]
    assert before >= 0
    yield before
    gc.collect()
    assert budget.health()["used_bytes"] == before


@pytest.mark.parametrize("clone", [copy, deepcopy])
def test_claim_copy_has_independent_admission_and_close_order(initial, clone):
    original = budget.Claim(32)
    other = clone(original)
    assert other is not original and other.size == original.size == 32
    assert budget.health()["used_bytes"] == initial + 64
    original.close()
    original.close()
    del original
    gc.collect()
    assert budget.health()["used_bytes"] == initial + 32
    other.grow(16)
    assert budget.health()["used_bytes"] == initial + 48
    other.close()
    other.close()


def test_deepcopy_shared_claim_is_acquired_once_per_copied_owner_graph(initial):
    with budget.Claim(64) as original:
        cloned = deepcopy([original, original])
        assert cloned[0] is cloned[1] and cloned[0] is not original
        assert budget.health()["used_bytes"] == initial + 128
        del cloned
        gc.collect()
        assert budget.health()["used_bytes"] == initial + 64


@pytest.mark.parametrize("clone", [copy, deepcopy])
def test_overflow_copy_preserves_original_reservation(initial, monkeypatch, clone):
    with budget.Claim(64) as original:
        monkeypatch.setattr(budget, "LIMIT_BYTES", initial + 127)
        with pytest.raises(ValueError, match="partition_resume_required"):
            clone(original)
        gc.collect()
        assert original.size == 64 and budget.health()["used_bytes"] == initial + 64


def test_live_claim_is_not_a_serializable_reservation(initial):
    with budget.Claim(32) as original:
        with pytest.raises(TypeError, match="claim_process_local"):
            pickle.dumps(original)
        assert original.size == 32 and budget.health()["used_bytes"] == initial + 32


def test_parallel_copies_and_repeated_close_keep_exact_admission(initial):
    workers = 8
    acquired, release = Barrier(workers + 1), Barrier(workers + 1)
    with budget.Claim(32) as original:

        def worker(_):
            other = deepcopy(original)
            other.grow(16)
            acquired.wait(timeout=10)
            release.wait(timeout=10)
            other.close()
            other.close()

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(worker, n) for n in range(workers)]
            acquired.wait(timeout=10)
            assert budget.health()["used_bytes"] == initial + 32 + workers * 48
            release.wait(timeout=10)
            for future in futures:
                future.result()
        assert budget.health()["used_bytes"] == initial + 32


@pytest.mark.parametrize("clone", [copy, deepcopy])
def test_resident_facts_copy_does_not_charge_append_again(initial, clone):
    original = ResidentFacts([{"record_id": 1, "values": [1, 2]}])
    amount = original.claim.size
    other = clone(original)
    assert other == original and other.claim is not original.claim
    assert other.claim.size == amount
    assert budget.health()["used_bytes"] == initial + 2 * amount
    if clone is deepcopy:
        other[0]["values"].append(3)
        assert original[0]["values"] == [1, 2]
    other.append({"record_id": 2})
    assert len(original) == 1 and other.claim.size > amount
    del other
    gc.collect()
    assert budget.health()["used_bytes"] == initial + amount
    del original


def test_nested_path_partition_copies_keep_shared_owner_and_data_aliases(initial):
    original, partition = ResidentPaths(), ResidentPaths()
    rows = BoundedRows(partition.claim)
    rows.append({"price": 10})
    partition["trade"] = {"ticks": rows}
    original.partitions.append(partition)
    original.update(partition)
    amount = partition.claim.size
    other = deepcopy(original)
    assert other["trade"] is other.partitions[0]["trade"]
    assert other["trade"]["ticks"].claim is other.partitions[0].claim
    assert other.partitions[0].claim is not partition.claim
    assert other.partitions[0].claim.size == amount
    assert budget.health()["used_bytes"] == initial + 2 * amount
    del original, partition, rows
    gc.collect()
    assert budget.health()["used_bytes"] == initial + amount
    del other


def test_failed_resident_clone_releases_only_new_claims_even_with_retained_memo(
    initial,
):
    class Broken:
        def __deepcopy__(self, memo):
            raise RuntimeError("fixture_copy_failed")

    original = ResidentFacts([{"record_id": 1}])
    original.broken = Broken()
    amount = original.claim.size
    marker = object()
    memo = {id(marker): marker}
    with pytest.raises(RuntimeError, match="fixture_copy_failed") as failure:
        deepcopy(original, memo)
    # Keep both traceback and caller memo alive while checking reservations.
    assert failure.value is not None and memo == {id(marker): marker}
    assert (
        original.claim.size == amount
        and budget.health()["used_bytes"] == initial + amount
    )
    del failure, original


def test_nested_clone_overflow_releases_earlier_clone_but_keeps_all_originals(
    initial, monkeypatch
):
    original = ResidentFacts([{"record_id": 1}])
    original.second_owner = budget.Claim(64)
    amount = original.claim.size
    monkeypatch.setattr(budget, "LIMIT_BYTES", initial + amount * 2 + 64)
    memo = {}
    with pytest.raises(ValueError, match="partition_resume_required") as failure:
        deepcopy(original, memo)
    assert failure.value is not None and memo == {}
    assert original.claim.size == amount and original.second_owner.size == 64
    assert budget.health()["used_bytes"] == initial + amount + 64
    del failure, original


def test_quantity_feature_generation_binds_the_shared_budget_reader(
    tmp_path, monkeypatch
):
    from src.engine.scalping import initial_quantity_policy as policy
    from src.engine.scalping import initial_quantity_source_cache as cache

    monkeypatch.setattr(
        policy, "_quantity_capture_lifecycle_sources", lambda *a: ([], {})
    )
    raw = tmp_path / "pipeline_events" / "pipeline_events_2026-10-16.jsonl"
    raw.parent.mkdir()
    raw.write_text("")
    trades = [{"entry_date": "2026-10-16"}]
    before = cache.fingerprint(trades, raw, 600)
    helper = Path(budget.__file__)
    original_read = Path.read_bytes
    original = original_read(helper)
    assert (
        before["reader"]["lifecycle/research_input_budget.py"]
        == hashlib.sha256(original).hexdigest()
    )

    def changed(path):
        return (
            original + b"\n# changed reservation reader\n"
            if path == helper
            else original_read(path)
        )

    monkeypatch.setattr(Path, "read_bytes", changed)
    after = cache.fingerprint(trades, raw, 600)
    assert after != before
    assert {k: v for k, v in after.items() if k != "reader"} == {
        k: v for k, v in before.items() if k != "reader"
    }
