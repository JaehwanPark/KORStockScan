import hashlib
import json
import gzip
from datetime import datetime, timedelta

import pytest

from src.engine import buy_funnel_sentinel as buy
from src.engine.monitoring import sentinel_compact_store as store


def event(at, stage, *, symbol="000001", attempt="a"):
    row = dict(
        emitted_at=at,
        pipeline="ENTRY_PIPELINE",
        stage=stage,
        stock_code=symbol,
        stock_name="Example",
        record_id="one",
        fields={"evaluation_attempt_id": attempt, "reason": "blocked"},
    )
    row["_sentinel_index_sha"] = hashlib.sha256(
        json.dumps(row, sort_keys=True).encode()
    ).hexdigest()
    return buy._event_from_cache_row(row)


@pytest.mark.parametrize("seconds", [0, 1, 60, 3600])
def test_cached_summary_preserves_exact_cutoff_and_full_native_result(
    tmp_path, monkeypatch, seconds
):
    monkeypatch.setattr(buy, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store, "report_code_contract", lambda: "code-v1")
    events = [
        event("2026-10-13T09:01:00", "ai_confirmed"),
        event("2026-10-13T09:02:00", "budget_pass"),
        event("2026-10-13T09:02:00", "order_leg_sent"),
    ]
    start = datetime(2026, 10, 13, 9)
    end = datetime(2026, 10, 13, 9, 2) + timedelta(seconds=seconds)
    expected = buy._calculate_event_summary(events, start_at=start, end_at=end)
    assert buy._summarize_events(events, start_at=start, end_at=end) == expected
    assert buy._summarize_events(events, start_at=start, end_at=end) == expected
    late = event("2026-10-13T09:01:30", "latency_block", attempt="b")
    changed = sorted(events + [late], key=lambda e: e.emitted_at)
    assert buy._summarize_events(
        changed, start_at=start, end_at=end
    ) == buy._calculate_event_summary(changed, start_at=start, end_at=end)


def test_summary_reuses_identical_population_after_last_event(tmp_path, monkeypatch):
    monkeypatch.setattr(buy, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store, "report_code_contract", lambda: "code-v1")
    events = [event("2026-10-12T09:01:00", "ai_confirmed")]
    start = datetime(2026, 10, 12, 8)
    expected = buy._summarize_events(
        events, start_at=start, end_at=datetime(2026, 10, 12, 19)
    )

    def forbidden(*a, **kw):
        pytest.fail("unchanged full population recomputed")

    monkeypatch.setattr(buy, "_calculate_event_summary", forbidden)
    later = buy._summarize_events(
        events, start_at=start, end_at=datetime(2026, 10, 12, 19, 5)
    )
    assert later == dict(expected, end_at="2026-10-12T19:05:00")


def test_slim_projection_invalidates_same_size_source_change(tmp_path):
    source = tmp_path / "summary.jsonl"
    source.write_text("a")
    calls = []

    def load():
        calls.append(1)
        return [{"value": source.read_text()}]

    assert store.slim_summary_projection(source, load, contract="v1") == [
        {"value": "a"}
    ]
    assert store.slim_summary_projection(source, load, contract="v1") == [
        {"value": "a"}
    ]
    assert len(calls) == 1
    source.write_text("b")
    assert store.slim_summary_projection(source, load, contract="v1") == [
        {"value": "b"}
    ]
    assert len(calls) == 2


def test_compressed_identity_preserves_order_independent_exact_fields(tmp_path):
    fields = {"z": "한글" * 50000, "a": "1", "venue": "KRX"}
    cache = tmp_path / "rows.jsonl"
    cache.write_text(json.dumps({"fields": fields}) + "\n")
    row = next(store.indexed_rows(cache, previous_stamp=None, expected_count=1))
    compact = row["fields"]
    assert dict(compact.items()) == fields
    assert compact.get("ai_call_trigger_reason") is None
    assert compact["venue"] == "KRX"
    assert store.fields_identity(compact) == store.fields_identity(
        dict(reversed(list(fields.items())))
    )
    assert store.fields_identity(compact) != store.fields_identity(dict(fields, a="2"))


def test_optional_memo_write_failure_retains_native_result(tmp_path, monkeypatch):
    def fail(*a, **kw):
        raise OSError("no_space")

    monkeypatch.setattr(store.tempfile, "mkstemp", fail)
    assert store.summary_memo(tmp_path, "a" * 64, lambda: {"unknown": None}) == {
        "unknown": None
    }


@pytest.mark.parametrize("damage", ["row", "payload"])
def test_index_population_and_lazy_payload_damage_rebuild(tmp_path, damage):
    import sqlite3

    cache = tmp_path / "rows.jsonl"
    cache.write_text(json.dumps({"fields": {"reason": "r" * 1000}}) + "\n")
    rows = list(store.indexed_rows(cache, previous_stamp=None, expected_count=1))
    assert rows[0]["fields"]["reason"] == "r" * 1000  # Large hot value stays lazy.
    with sqlite3.connect(cache.with_suffix(".compact.sqlite")) as conn:
        conn.execute(
            "DELETE FROM rows"
            if damage == "row"
            else "UPDATE payloads SET body=X'6162'"
        )
    with pytest.raises(ValueError, match="corrupt"):
        rows = list(store.indexed_rows(cache, previous_stamp=None, expected_count=1))
        rows[0]["fields"]["reason"]
    rows = list(store.indexed_rows(cache, previous_stamp=None, expected_count=1))
    assert rows[0]["fields"]["reason"] == "r" * 1000


def test_slim_projection_cannot_publish_or_return_mixed_generation(tmp_path):
    import pytest
    from src.engine.monitoring import sentinel_compact_store as owner

    path = tmp_path / "summary.jsonl"
    path.write_text("first\n")

    def race():
        path.write_text("different generation\n")
        return [{"event_count": 1}]

    with pytest.raises(ValueError, match="source_changed_during_read"):
        owner.slim_summary_projection(path, race, contract="strict-v1")
    assert not path.with_name(path.name + ".sentinel-slim.json").exists()


def _archive_fixture(tmp_path):
    cache = tmp_path / "events.jsonl"
    rows = [
        {"stage": "one", "fields": {"venue": "KRX", "reason": "한글" * 50}},
        {"stage": "two", "fields": {"venue": "NXT", "reason": "second"}},
    ]
    raw = b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows)
    cache.write_bytes(raw)
    original = store.stamp(cache)
    plain = list(store.indexed_rows(cache, previous_stamp=None, expected_count=len(rows)))
    expected = [(r["stage"], dict(r["fields"].items())) for r in plain]
    archive = tmp_path / "events.jsonl.gz"
    archive.write_bytes(gzip.compress(raw, mtime=0))
    binding = dict(source_generation=original, logical_sha256=hashlib.sha256(raw).hexdigest(),
                   logical_size=len(raw), archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                   archive_generation=store.stamp(archive))
    return cache, archive, binding, expected


def test_archived_successor_reuses_logical_offsets_and_preserves_plain_index(tmp_path):
    import sqlite3
    cache, archive, binding, expected = _archive_fixture(tmp_path)
    original_index = cache.with_suffix(".compact.sqlite")
    original_bytes = original_index.read_bytes()
    cache.unlink()  # Isolated fixture only; production retention remains separate.
    result = list(store.indexed_rows(cache, previous_stamp=None, expected_count=2,
                                     archive_binding=binding))
    assert [(r["stage"], dict(r["fields"].items())) for r in result] == expected
    assert original_index.read_bytes() == original_bytes
    index = tmp_path / "events.jsonl.gz.compact.sqlite"
    with sqlite3.connect(index) as db:
        state = json.loads(db.execute("SELECT body FROM state").fetchone()[0])
        offsets = [x[0] for x in db.execute("SELECT offset FROM rows ORDER BY offset")]
    assert state["generation"] == binding["archive_generation"]
    assert state["archive_binding"]["source_generation"] == binding["source_generation"]
    assert state["offset"] == binding["logical_size"] == offsets[-1]
    second = list(store.indexed_rows(cache, previous_stamp=None, expected_count=2,
                                     archive_binding=binding))
    assert [(r["stage"], dict(r["fields"].items())) for r in second] == expected


def test_archive_failed_reindex_rolls_back_previous_index(tmp_path):
    import sqlite3

    cache, archive, binding, _ = _archive_fixture(tmp_path)
    cache.unlink()
    list(store.indexed_rows(cache, previous_stamp=None, expected_count=2,
                            archive_binding=binding))
    index = tmp_path / "events.jsonl.gz.compact.sqlite"
    with sqlite3.connect(index) as db:
        old_state = db.execute("SELECT body FROM state").fetchone()
        old_rows = db.execute("SELECT offset, body, sha FROM rows ORDER BY offset").fetchall()
    damaged = bytearray(archive.read_bytes())
    damaged[-8] ^= 1
    archive.write_bytes(damaged)
    changed = dict(binding, archive_sha256=hashlib.sha256(damaged).hexdigest(),
                   archive_generation=store.stamp(archive))
    with pytest.raises((ValueError, OSError, EOFError)):
        list(store.indexed_rows(cache, previous_stamp=None, expected_count=2,
                                archive_binding=changed))
    with sqlite3.connect(index) as db:
        assert db.execute("SELECT body FROM state").fetchone() == old_state
        assert db.execute("SELECT offset, body, sha FROM rows ORDER BY offset").fetchall() == old_rows


@pytest.mark.parametrize("damage", ["archive_sha", "logical_sha", "size", "crc", "generation", "append"])
def test_archived_successor_rejects_mixed_or_corrupt_generation(tmp_path, damage):
    cache, archive, binding, _ = _archive_fixture(tmp_path)
    cache.unlink()
    if damage == "archive_sha":
        binding["archive_sha256"] = "0" * 64
    elif damage == "logical_sha":
        binding["logical_sha256"] = "0" * 64
    elif damage == "size":
        binding["logical_size"] += 1
    elif damage == "crc":
        broken = bytearray(archive.read_bytes()); broken[-8] ^= 1; archive.write_bytes(broken)
        binding["archive_sha256"] = hashlib.sha256(broken).hexdigest()
        binding["archive_generation"] = store.stamp(archive)
    elif damage == "generation":
        binding["archive_generation"][1] += 1
    previous = binding["source_generation"] if damage == "append" else None
    with pytest.raises((ValueError, OSError, EOFError)):
        list(store.indexed_rows(cache, previous_stamp=previous, expected_count=2,
                                archive_binding=binding))


def test_archived_successor_rejects_reappearing_plain_generation(tmp_path):
    cache, archive, binding, _ = _archive_fixture(tmp_path)
    with pytest.raises(ValueError, match="namespace_changed"):
        list(store.indexed_rows(cache, previous_stamp=None, expected_count=2,
                                archive_binding=binding))


def test_archived_successor_reuses_native_invocation_digest(tmp_path, monkeypatch):
    from src.engine.infrastructure import validation_digest_session as digest_owner

    cache, archive, binding, expected = _archive_fixture(tmp_path)
    cache.unlink()
    monkeypatch.setattr(digest_owner, "MIN_BYTES", 1)
    cold = list(store.indexed_rows(cache, previous_stamp=None, expected_count=2,
                                   archive_binding=binding))
    assert [(r["stage"], dict(r["fields"].items())) for r in cold] == expected
    with digest_owner.postclose_session(tmp_path, "2026-10-28") as session:
        for _ in range(2):
            rows = list(store.indexed_rows(cache, previous_stamp=None, expected_count=2,
                                           archive_binding=binding))
            assert [(r["stage"], dict(r["fields"].items())) for r in rows] == expected
        assert session.stats["full_reads"] == 1
        assert session.stats["reused_reads"] == 1
        archive.write_bytes(archive.read_bytes() + b"changed")
        with pytest.raises(ValueError, match="generation_changed"):
            list(store.indexed_rows(cache, previous_stamp=None, expected_count=2,
                                    archive_binding=binding))


def test_archived_successor_uses_resolved_shared_mount_and_rejects_alias(tmp_path):
    physical = tmp_path / "physical"; physical.mkdir()
    cache, archive, binding, expected = _archive_fixture(physical)
    cache.unlink()
    alias = tmp_path / "release-data"; alias.symlink_to(physical, target_is_directory=True)
    with pytest.raises(ValueError, match="namespace_changed"):
        list(store.indexed_rows(alias / cache.name, previous_stamp=None, expected_count=2,
                                archive_binding=binding))
    resolved = (alias / cache.name).resolve()
    rows = list(store.indexed_rows(resolved, previous_stamp=None, expected_count=2,
                                   archive_binding=binding))
    assert [(r["stage"], dict(r["fields"].items())) for r in rows] == expected
