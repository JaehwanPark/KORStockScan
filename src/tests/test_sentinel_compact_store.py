import hashlib
import json
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
