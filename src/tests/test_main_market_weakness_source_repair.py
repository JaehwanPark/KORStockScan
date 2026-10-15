"""Production-shaped retained inputs and adversarial advisory-only repairs."""

import copy
from datetime import datetime, timedelta
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import time

import pytest

from src.engine.automation import main_market_weakness_research as A
from src.engine.automation import main_market_weakness_research_notify as N
from src.engine.scalping import market_weakness_research as R
from src.tests.test_main_market_weakness_research import (
    DAY,
    observation,
    row,
    trace,
    favorable,
    registry,
)


def native_capture():
    at = DAY + "T09:01:10+09:00"
    epoch = datetime.fromisoformat(at).timestamp()
    event = dict(
        at=at,
        epoch=epoch,
        symbol="005930",
        event_id="native-event",
        canonical_opportunity_id="canonical",
        source_item="005930_AL",
        native_epoch=3,
        native_sequence=7,
        venue="SOR",
        session="SOR_REGULAR",
        entry_ask=100,
        volume_ratio_60s=0.5,
        drawdown_5m_pct=0.2,
    )
    payload = dict(
        stock_code="005930",
        evaluation_attempt_id="attempt",
        entry_machine_input_as_of=epoch,
    )
    assessment = dict(
        event=event,
        action="ENTER_NOW",
        event_id=event["event_id"],
        opportunity_key="canonical",
        cell_key="samsung|REGULAR|ALL",
    )
    captured = DAY + "T09:01:11+09:00"
    native = dict(
        bundle_sha256="b" * 64,
        pid=123,
        process_start_ticks="456",
        captured_at=captured,
        event_id=event["event_id"],
        snapshot_read_at=epoch + 0.5,
        exact_payload_sha256=R.native_digest(payload),
        assessment_sha256=R.native_digest(assessment),
    )
    body = dict(
        schema="mechanistic_entry_observation_v1",
        redacted=False,
        provider_called=False,
        captured_at=captured,
        bundle_sha256=native["bundle_sha256"],
        label_context=dict(
            stock_code="005930", evaluation_attempt_id="attempt", comment="검증"
        ),
        source=dict(exact_payload=payload, assessment=assessment),
        runtime_consumption=dict(
            pid=123,
            process_start_ticks="456",
            bundle_sha256=native["bundle_sha256"],
            continuous_reversal=native,
        ),
        evaluation_role="operating",
        **R.AUTH,
    )
    body["machine_observation_sha256"] = R.native_digest(body)
    t = trace()
    t.update(
        decision_ts=DAY + "T09:01:12+09:00",
        evaluation_attempt_id="attempt",
        entry_mechanistic_action="ENTER_NOW",
        machine_bundle_sha256=native["bundle_sha256"],
        continuous_reversal_consumption=native,
        machine_observation_sha256=body["machine_observation_sha256"],
    )
    return body, t


def write_gzip(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wb") as handle:
        handle.write(value)


def test_gzip_only_day_discovery_and_reader_without_operating_directory(
    tmp_path, monkeypatch
):
    data = tmp_path / "data"
    path = data / "ai_decision_trace" / f"ai_decision_trace_{DAY}.jsonl.gz"
    write_gzip(path, (json.dumps(trace()) + "\n").encode())
    assert DAY in A.discover_dates(data, dict(evidence_start_date="2026-09-29"))
    selected = A.source_plan(data, DAY)
    assert len(selected) == 1 and selected[0]["compressed"]
    obs = data / "report/market_weakness_observations" / DAY / "one.json"
    A.atomic(obs, observation())
    monkeypatch.setattr(A, "listing_lookup", lambda *a: (lambda _: "KOSPI", None))
    result = A.process_date(data, DAY, stop_at=time.monotonic() + 10)
    cursor = A.read_json(A.namespace(data) / DAY / "cursor.json")
    assert result["delta"] == 1
    assert A.read_json(cursor["daily_path"])["census"]["projected_rows"] == 1
    assert A.process_date(data, DAY, stop_at=time.monotonic() + 10)["delta"] == 0


def test_small_json_gzip_aliases_strict_limit_and_conflict(tmp_path):
    p = tmp_path / "source.json"
    write_gzip(Path(str(p) + ".gz"), b'{"value":1}')
    value, receipt = A.read_source_json(p)
    assert value == {"value": 1} and receipt["compressed"]
    p.write_text('{"value": 1}')
    assert A.read_source_json(p)[0] == value
    p.write_text('{"value":2}')
    with pytest.raises(ValueError, match="alias_conflict"):
        A.read_source_json(p)
    p.unlink()
    with pytest.raises(ValueError, match="decoded_size_limit"):
        A.read_source_json(p, limit=2)


@pytest.mark.parametrize("raw", [b'{"x":1,"x":2}', b'{"x":NaN}', b"\xff"])
def test_strict_source_does_not_hide_bad_rows(raw):
    with pytest.raises((ValueError, UnicodeError)):
        A.strict_json(raw)


def test_native_stored_body_binds_trace_without_assessment_in_trace(tmp_path):
    body, t = native_capture()
    assert "entry_mechanistic_policy_decision" not in t
    native, reason = R.project_native_observation(body, DAY)
    assert reason is None
    native["source_ref"] = {"path": "retained", "offset": 0}
    projected = R.project_trace(t, DAY, "KOSPI")[0]
    R.bind_native(projected, native)
    assert projected["identity_grade"] == "canonical"
    assert projected["entry_ask"] == 100
    assert projected["features"]["volume_ratio_60s"] == 0.5
    label = dict(
        projected,
        decision_origin="confirmation_replay",
        auxiliary_hash=None,
        outcome="W",
        outcome_reason=None,
        source_ref={"label": "retained"},
    )
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE labels(id TEXT PRIMARY KEY,row TEXT,conflict INTEGER)")
    A._index_label(db, label)
    A.bind_natural_label(projected, db)
    assert projected["outcome"] == "W"
    db.close()


@pytest.mark.parametrize(
    "field,value", [("pid", 999), ("assessment_sha256", "wrong"), ("event_id", "wrong")]
)
def test_exact_native_receipt_mismatch_never_promotes_trace(field, value):
    body, t = native_capture()
    native = R.project_native_observation(body, DAY)[0]
    t = copy.deepcopy(t)
    t["continuous_reversal_consumption"][field] = value
    projected = R.project_trace(t, DAY, "KOSPI")[0]
    R.bind_native(projected, native)
    assert projected["identity_grade"] == "trace_only"
    assert projected["entry_ask"] is None and projected["outcome"] == "U"


def test_native_body_corruption_and_final_source_invalid_are_not_enter():
    body, t = native_capture()
    bad = copy.deepcopy(body)
    bad["source"]["assessment"]["event"]["entry_ask"] = 101
    assert (
        R.project_native_observation(bad, DAY)[1]
        == "native_observation_binding_invalid"
    )
    t["entry_mechanistic_action"] = "source_invalid"
    projected = R.project_trace(t, DAY, "KOSPI")[0]
    R.bind_native(projected, R.project_native_observation(body, DAY)[0])
    assert projected["machine_action"] == "source_invalid"


def test_native_index_stream_and_duplicate_preserve_first_receipt(tmp_path):
    body, _ = native_capture()
    p = tmp_path / "payload.jsonl.gz"
    write_gzip(p, ((json.dumps(body, ensure_ascii=False) + "\n") * 2).encode())
    source = A.stream_source(tmp_path / "payload.jsonl", "native_observations")
    chunks = list(A.native_records(source, DAY, tmp_path, stop_at=time.monotonic() + 5))
    rows = [r for chunk in chunks for r in chunk[0]]
    assert len(rows) == 2 and chunks[-1][2]
    cursor = dict(source_date=DAY, generation="fixture")
    db = A.native_index(tmp_path, cursor)
    A.index_native_rows(db, rows, source["path"])
    assert db.execute("SELECT count(*) FROM native WHERE conflict=0").fetchone()[0] == 1
    db.close()


def test_confirmed_weakness_uses_two_observations_and_three_recoveries():
    at = datetime.fromisoformat(DAY + "T09:00:00+09:00")
    observations = [
        observation(
            (at + timedelta(minutes=n)).isoformat(),
            "SINGLE_MARKET_WEAKNESS" if n < 2 else "RECOVERY_EVIDENCE",
        )
        for n in range(5)
    ]
    reconstructed = R.reconstruct_latches(observations)
    assert [o["reconstructed_active"]["KOSPI"] for o in reconstructed] == [
        False,
        True,
        True,
        True,
        False,
    ]
    episodes = [o["reconstructed_episode_ids"].get("KOSPI") for o in reconstructed]
    assert episodes[1] == episodes[2] == episodes[3] and episodes[4] is None
    r = row()
    r["decision_ts"] = (at + timedelta(seconds=1)).isoformat()
    assert R.attach_joins(r, reconstructed)["joins"]["0"]["state"] != "WEAKNESS"
    r["decision_ts"] = (at + timedelta(seconds=61)).isoformat()
    assert R.attach_joins(r, reconstructed)["joins"]["0"]["state"] == "WEAKNESS"


def test_latch_duplicate_and_stale_gap_cannot_confirm():
    a = observation()
    late = observation(DAY + "T09:06:00+09:00")
    reconstructed = R.reconstruct_latches([a, a, late])
    assert len(reconstructed) == 2
    assert reconstructed[-1]["reconstructed_active"]["KOSPI"] is False


def test_verified_scoped_cohort_survives_unrelated_bundle_but_not_definition_change():
    a = row()
    a["cohort_contract"] = dict(
        verified=True,
        machine_payload_sha256="payload",
        feature_kernel={"kernel": "hash"},
    )
    b = dict(a, machine_hash="another-publication")
    assert R.scope_key(a) == R.scope_key(b)
    b["cohort_contract"] = dict(a["cohort_contract"], machine_payload_sha256="changed")
    assert R.scope_key(a) != R.scope_key(b)


def test_added_only_pair_and_unknown_extremes():
    pair = dict(
        selected=dict(W=2, F=2, U=1),
        excluded=dict(W=0, F=0, U=0),
        added=dict(W=3, F=0, U=1),
    )
    assert R.pair_delta(pair) > 0
    # Exhaustively check the small shared-U case against the bounded endpoint rule.
    values = [(5 + x) / 9 - (2 + x) / 5 for x in range(2)]
    assert R.pair_delta(pair, worst_u=True) == min(values)


def test_machine_filter_accepts_no_auxiliary_but_requires_verified_axis():
    r = row(value=0.5)
    r.update(
        auxiliary_verdict="not_called", auxiliary_hash=None, machine_action="ENTER_NOW"
    )
    axis = dict(verified=True, role="baseline_prior", axis="volume_ratio_60s")
    d = dict(
        kind="machine_confirmation_filter_cf",
        axis="volume_ratio_60s",
        after=1,
        operator="ge",
        axis_contract=axis,
        weakness_index_max_pct=-1,
    )
    assert R.selection(r, {"definition": d}, r["joins"]["0"]) is False
    d["axis_contract"] = dict(axis, role="hard_safety")
    assert R.selection(r, {"definition": d}, r["joins"]["0"]) is None


def test_candidate_statistics_checkpoint_resume_uses_completed_candidate():
    a = R.Aggregator(registry(row()))
    favorable(a)
    cache = {}

    def checkpoint(sid, cid, value):
        if value is None:
            return cache.get((sid, cid))
        cache[sid, cid] = copy.deepcopy(value)

    first = a.comparison("g", checkpoint=checkpoint)
    assert cache
    assert a.comparison("g", checkpoint=checkpoint) == first
    with pytest.raises(R.ResearchBudgetExceeded):
        a.comparison("g", gate=lambda: False)
    a.close()


def test_machine_preview_does_not_claim_auxiliary_pass_or_added_opportunities():
    a = R.Aggregator(registry(row()))
    favorable(a)
    c = a.comparison("g")["comparisons"][0]
    c = copy.deepcopy(c)
    c["definition"].update(
        kind="machine_confirmation_filter_cf",
        operator="ge",
        before=0.2,
        axis_contract=dict(verified=True, role="baseline_prior"),
    )
    assert N.advisory_eligible(c)
    message = N.preview(c)
    assert "기계 단독" in message and "실제 보조 PASS 이후" not in message
    c.update(excluded_opportunities=0, added_opportunities=1)
    assert not N.advisory_eligible(c)
    a.close()


def test_phase_receipt_preserves_completed_daily_for_next_reservation(tmp_path):
    A.phase_receipt(tmp_path, DAY, "daily", "cumulative_pending")
    assert A.unfinished_phase(tmp_path, DAY, dict(generation="daily"))
    A.phase_receipt(tmp_path, DAY, "daily", "completed")
    assert not A.unfinished_phase(tmp_path, DAY, dict(generation="daily"))


def rehash_native(body):
    native = body["runtime_consumption"]["continuous_reversal"]
    native.update(
        exact_payload_sha256=R.native_digest(body["source"]["exact_payload"]),
        assessment_sha256=R.native_digest(body["source"]["assessment"]),
    )
    body.pop("machine_observation_sha256", None)
    body["machine_observation_sha256"] = R.native_digest(body)


def test_nonessential_redaction_is_not_a_missing_event():
    body, _ = native_capture()
    body["redacted"] = True
    body["runtime_consumption"]["continuous_reversal"]["signal_token"] = "[REDACTED]"
    rehash_native(body)
    projected, reason = R.project_native_observation(body, DAY)
    assert reason is None and projected["event"]["entry_ask"] == 100
    assert "signal_token" not in projected["native_receipt"]
    body["source"]["assessment"]["event"]["event_id"] = "[REDACTED]"
    body["source"]["assessment"]["event_id"] = "[REDACTED]"
    body["runtime_consumption"]["continuous_reversal"]["event_id"] = "[REDACTED]"
    rehash_native(body)
    assert (
        R.project_native_observation(body, DAY)[1]
        == "native_event_required_field_redacted_or_missing"
    )


@pytest.mark.parametrize(
    "mutation", ["missing_event_id", "future_clock", "negative_ask", "wrong_date"]
)
def test_native_critical_event_contract_is_not_reconstructed(mutation):
    body, _ = native_capture()
    event = body["source"]["assessment"]["event"]
    if mutation == "missing_event_id":
        event.pop("event_id")
    elif mutation == "future_clock":
        body["runtime_consumption"]["continuous_reversal"]["snapshot_read_at"] += 100
    elif mutation == "negative_ask":
        event["entry_ask"] = -1
    else:
        event["at"] = "2026-10-09T09:01:10+09:00"
    rehash_native(body)
    assert R.project_native_observation(body, DAY)[0] is None


@pytest.mark.parametrize("role", ["operating", "probe_observation"])
def test_native_nonentry_counts_without_inventing_event(role):
    body, t = native_capture()
    body["evaluation_role"] = role
    body["source"]["assessment"] = dict(
        action="BLOCK", reason="no_current_operating_signal"
    )
    body["runtime_consumption"]["continuous_reversal"]["event_id"] = None
    rehash_native(body)
    native = R.project_native_observation(body, DAY)[0]
    t["continuous_reversal_consumption"] = body["runtime_consumption"][
        "continuous_reversal"
    ]
    t["machine_observation_sha256"] = body["machine_observation_sha256"]
    t["entry_mechanistic_action"] = "BLOCK"
    r = R.project_trace(t, DAY, "KOSPI")[0]
    R.bind_native(r, native)
    assert r["native_binding_status"] == "verified" and r["entry_ask"] is None
    assert r["machine_action"] == "BLOCK" and r["outcome"] == "U"
    assert r["decision_origin"] == (
        "probe_observation" if role == "probe_observation" else "natural_decision"
    )


def master_payload(day):
    from src.tests.test_micro_reversion_symbol_master import (
        _master_payload,
        _producer_hash,
    )

    p = _master_payload()
    p["artifact_id"] = "main-ai-economic-reference-" + day + "-symbol-master"
    p.pop("content_sha256")
    p["content_sha256"] = _producer_hash(p)
    return p


def test_real_master_contract_gzip_future_exclusion_and_alias_conflict(tmp_path):
    folder = tmp_path / "report/micro_reversion_economic_reference"
    p = folder / ("micro_reversion_symbol_master_" + DAY + ".json")
    payload = master_payload(DAY)
    write_gzip(Path(str(p) + ".gz"), json.dumps(payload).encode())
    write_gzip(folder / "micro_reversion_symbol_master_2026-10-15.json.gz", b"invalid")
    lookup, receipt = A.listing_lookup(tmp_path, DAY)
    assert lookup("005930") == "KOSPI" and receipt["compressed"]
    assert lookup("000000") is None
    A.atomic(p, payload)
    assert A.listing_lookup(tmp_path, DAY)[0]("005930") == "KOSPI"
    A.atomic(p, dict(payload, verified=False))
    lookup, receipt = A.listing_lookup(tmp_path, DAY)
    assert lookup("005930") is None and receipt["status"] == "source_invalid"


def test_gzip_trace_has_both_physical_and_decoded_receipt(tmp_path):
    payload = (json.dumps(trace()) + "\n").encode()
    p = tmp_path / "trace.jsonl.gz"
    write_gzip(p, payload)
    s = A.stream_source(tmp_path / "trace.jsonl", "natural_trace")
    chunks = list(
        A.gzip_trace_records(s, DAY, lambda _: "KOSPI", stop_at=time.monotonic() + 5)
    )
    proof = chunks[-1][4]
    assert proof["physical_sha256"] == hashlib.sha256(p.read_bytes()).hexdigest()
    assert proof["decoded_sha256"] == hashlib.sha256(payload).hexdigest()


def test_crc_failure_discards_previously_projected_chunks(tmp_path, monkeypatch):
    data = tmp_path / "data"
    p = data / "ai_decision_trace" / f"ai_decision_trace_{DAY}.jsonl.gz"
    write_gzip(p, ((json.dumps(trace()) + "\n") * 3).encode())
    broken = bytearray(p.read_bytes())
    broken[-8] ^= 1
    p.write_bytes(broken)
    monkeypatch.setattr(A, "CHUNK_ROWS", 1)
    monkeypatch.setattr(A, "listing_lookup", lambda *a: (lambda _: "KOSPI", None))
    A.process_date(data, DAY, stop_at=time.monotonic() + 5)
    cursor = A.read_json(A.namespace(data) / DAY / "cursor.json")
    daily = A.read_json(cursor["daily_path"])
    assert daily["census"].get("projected_rows", 0) == 0
    assert cursor["partitions"] == []
    assert cursor["gaps"]["compressed_source_contract_invalid"] == 1


def test_compressed_interruption_does_not_rescan_prefix(tmp_path, monkeypatch):
    data = tmp_path / "data"
    p = data / "ai_decision_trace" / f"ai_decision_trace_{DAY}.jsonl.gz"
    write_gzip(p, (json.dumps(trace()) + "\n").encode())
    monkeypatch.setattr(A, "listing_lookup", lambda *a: (lambda _: "KOSPI", None))
    original = A.gzip_trace_records

    def interrupted(*args, **kwargs):
        for rows, offset, _, gaps, proof in original(*args, **kwargs):
            yield rows, offset, False, gaps, proof
            raise A.Deferred("simulated_budget")

    monkeypatch.setattr(A, "gzip_trace_records", interrupted)
    with pytest.raises(A.Deferred):
        A.process_date(data, DAY, stop_at=time.monotonic() + 5)
    cursor = A.read_json(A.namespace(data) / DAY / "cursor.json")
    assert cursor["partitions"] == [] and cursor["source_index"] == 1
    monkeypatch.setattr(
        A, "gzip_trace_records", lambda *a, **k: pytest.fail("prefix rescanned")
    )
    A.process_date(data, DAY, stop_at=time.monotonic() + 5)
    cursor = A.read_json(A.namespace(data) / DAY / "cursor.json")
    assert cursor["gaps"]["compressed_resume_unavailable"] == 1


def test_native_cache_corruption_cannot_bind_trace(tmp_path):
    body, t = native_capture()
    native = R.project_native_observation(body, DAY)[0]
    db = A.native_index(tmp_path, dict(source_date=DAY, generation="fixture"))
    A.index_native_rows(db, [native], "fixture")
    saved = json.loads(db.execute("SELECT row FROM native").fetchone()[0])
    saved["event"]["entry_ask"] = 999
    db.execute("UPDATE native SET row=?", (json.dumps(saved),))
    db.commit()
    with pytest.raises(ValueError, match="seal_invalid"):
        A.bind_trace_native(R.project_trace(t, DAY, "KOSPI")[0], db)
    db.close()


def test_label_conflicting_alias_or_route_is_not_borrowed():
    body, t = native_capture()
    projected = R.project_trace(t, DAY, "KOSPI")[0]
    R.bind_native(projected, R.project_native_observation(body, DAY)[0])
    label = dict(
        projected,
        decision_origin="confirmation_replay",
        auxiliary_hash=None,
        outcome="W",
        outcome_reason=None,
    )
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE labels(id TEXT PRIMARY KEY,row TEXT,conflict INTEGER)")
    A._index_label(db, label)
    db.execute(
        "UPDATE labels SET conflict=1 WHERE id=?", (projected["opportunity_id"],)
    )
    A.bind_natural_label(projected, db)
    assert (
        projected["outcome"] == "U"
        and projected["outcome_reason"] == "exact_label_binding_conflict"
    )
    db.execute("UPDATE labels SET conflict=0")
    projected["route"] = "KRX"
    A.bind_natural_label(projected, db)
    assert projected["outcome"] == "U"
    db.close()


def test_native_and_trace_gzip_integration_does_not_fabricate_auxiliary(
    tmp_path, monkeypatch
):
    body, t = native_capture()
    data = tmp_path / "data"
    write_gzip(
        data / "ai_decision_payloads" / f"ai_decision_payloads_{DAY}.jsonl.gz",
        (json.dumps(body) + "\n").encode(),
    )
    write_gzip(
        data / "ai_decision_trace" / f"ai_decision_trace_{DAY}.jsonl.gz",
        (json.dumps(t) + "\n").encode(),
    )
    monkeypatch.setattr(A, "listing_lookup", lambda *a: (lambda _: "KOSPI", None))
    A.process_date(data, DAY, stop_at=time.monotonic() + 5)
    cursor = A.read_json(A.namespace(data) / DAY / "cursor.json")
    projected = list(A.projection_rows(cursor["partitions"]))[0]
    assert projected["native_binding_status"] == "verified"
    assert projected["entry_ask"] == 100 and projected["identity_grade"] == "canonical"
    assert (
        projected["auxiliary_verdict"] == "not_called" and projected["outcome"] == "U"
    )
    assert len(A.read_json(cursor["manifest_path"])["stream_receipts"]) == 2


def test_semantic_id_ignores_global_but_keeps_numeric_definition():
    a = R.Aggregator(registry(row()))
    favorable(a)
    c = copy.deepcopy(a.comparison("g")["comparisons"][0])
    a.close()
    c["definition"].update(
        scope_parent_machine_payload_sha256="scoped",
        auxiliary_binding={"prompt": "fixed"},
    )
    d = copy.deepcopy(c)
    d["definition"].update(parent_hash="changed", auxiliary_hash="changed")
    d["scope"].update(machine_hash="changed", auxiliary_hash="changed")
    assert N.recommendation_id(c) == N.recommendation_id(d)
    d["definition"]["after"] = 123
    assert N.recommendation_id(c) != N.recommendation_id(d)


def test_migration_does_not_retract_sent_receipts(tmp_path):
    a = R.Aggregator(registry(row()))
    favorable(a)
    comparison = a.comparison("g")
    a.close()
    N.reconcile(
        tmp_path,
        comparison,
        send_enabled=True,
        gate=lambda: True,
        source_matches=lambda: True,
        parent_matches=lambda *a: True,
        transport=lambda _: dict(status="sent", message_id=123),
    )
    before = (tmp_path / "outbox/state.json").read_bytes()
    pending = R.seal(dict(comparison, comparisons=[], migration_pending=True))
    result = N.reconcile(
        tmp_path,
        pending,
        send_enabled=True,
        transport=lambda _: pytest.fail("migration transmitted"),
    )
    assert result["status"] == "deferred_migration_or_comparison"
    assert (tmp_path / "outbox/state.json").read_bytes() == before


def test_latest_deferred_keeps_original_completed_computation(tmp_path):
    completed = R.seal(
        dict(
            status="completed",
            cumulative_generation="old",
            daily_generation="daily",
            source_date=DAY,
            night_id=DAY,
            **R.AUTH,
        )
    )
    A.publish_night_status(tmp_path, completed)
    original = (tmp_path / "last_completed_computation.json").read_bytes()
    result = A.publish_night_status(
        tmp_path, R.seal(dict(status="deferred_resource_or_window", **R.AUTH))
    )
    assert result["latest_attempt"]["status"] == "deferred_resource_or_window"
    assert result["last_completed_computation"]["cumulative_generation"] == "old"
    assert (tmp_path / "last_completed_computation.json").read_bytes() == original


def test_rebind_preserves_notify_history_and_failure_restores_bytes(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace

    original = "35 7 * * * bash /preopen # THRESHOLD_CYCLE_PREOPEN\n0 12 * * * bash /eod # EOD\n"
    installed = [original]

    def runner(command, **kwargs):
        if "input" in kwargs:
            installed[0] = kwargs["input"]
        return SimpleNamespace(returncode=0, stdout=installed[0])

    monkeypatch.setattr(A, "alternate_schedule_census", lambda _: {})
    monkeypatch.setattr(A, "selected_optional_code", lambda _: "first-release")
    monkeypatch.setattr(A, "host_cron_zone", lambda: "Asia/Seoul")
    data = tmp_path / "data"
    A.namespace(data).parent.mkdir(parents=True)
    A.configure_optional_cron(data, tmp_path, notify_enabled=True, runner=runner)
    p = A.namespace(data) / "installation.json"
    before = A.read_json(p)
    before["enabled"] = False
    A.atomic(p, R.seal(before))
    before = A.read_json(p)
    monkeypatch.setattr(A, "selected_optional_code", lambda _: "second-release")
    A.configure_optional_cron(data, tmp_path, runner=runner)
    after = A.check_seal(A.read_json(p))
    assert after["notify_enabled"] is True and after["enabled"] is False
    for key in (
        "installed_at",
        "installed_source_date",
        "evidence_start_date",
        "selected_release_at_install",
    ):
        assert after[key] == before[key]
    assert after["selected_release_at_rebind"] == "second-release"
    saved_config, saved_cron = p.read_bytes(), installed[0]
    reads = [0]

    def broken_readback(command, **kwargs):
        result = runner(command, **kwargs)
        if command[-1] == "-l":
            reads[0] += 1
            if reads[0] == 2:
                result.stdout = "unexpected cron bytes"
        return result

    with pytest.raises(ValueError, match="readback_mismatch"):
        A.configure_optional_cron(data, tmp_path, runner=broken_readback)
    assert p.read_bytes() == saved_config and installed[0] == saved_cron


def source_bundle(data, *, role="bounded_tunable", unit="ratio"):
    axis = dict(
        role=role,
        axis="volume_ratio_60s",
        unit=unit,
        before=0.2,
        operator="ge",
        owner_definition_sha256="d" * 64,
    )
    machine = dict(
        branches=[dict(definition_sha256="d" * 64)], numeric_axis_contracts=[axis]
    )
    auxiliary = dict(binding=dict(prompt_version="frozen", arm="one"))
    kernels = {"continuous_reversal.py": "a" * 64}
    family = dict(
        machine_cells={
            "samsung|REGULAR|ALL": dict(
                routes=dict(SOR=dict(payload=machine, payload_sha256=R.digest(machine)))
            )
        },
        auxiliary_cells={
            "samsung|REGULAR|ALL": dict(
                routes=dict(
                    SOR=dict(payload=auxiliary, payload_sha256=R.digest(auxiliary))
                )
            )
        },
        contract_file_sha256=kernels,
        execution_code_sha256=R.digest(kernels),
        label_contract=R.LABEL,
    )
    family["family_sha256"] = R.digest(family)
    bundle = dict(continuous_reversal=family)
    bundle["bundle_sha256"] = R.digest(bundle)
    p = (
        data
        / "runtime/mechanistic_entry_policy/generations"
        / (bundle["bundle_sha256"] + ".json")
    )
    A.atomic(p, bundle)
    return bundle, p


@pytest.mark.parametrize(
    "role,unit,allowed",
    [
        ("bounded_tunable", "ratio", True),
        ("hard_safety", "ratio", False),
        ("bounded_tunable", "pct", False),
    ],
)
def test_scoped_machine_axis_requires_owner_role_and_unit(
    tmp_path, role, unit, allowed
):
    bundle, p = source_bundle(tmp_path, role=role, unit=unit)
    result = A.scope_contract(
        tmp_path, bundle["bundle_sha256"], "samsung|REGULAR|ALL", "SOR", cache={}
    )
    assert result["cohort_contract"]["verified"] is True
    assert bool(result["machine_axes"]) is allowed
    p.write_text(json.dumps(dict(bundle, continuous_reversal={})))
    assert (
        A.scope_contract(
            tmp_path, bundle["bundle_sha256"], "samsung|REGULAR|ALL", "SOR", cache={}
        )
        == {}
    )


def test_supported_machine_grid_works_without_auxiliary_population(tmp_path):
    bundle, _ = source_bundle(tmp_path)
    scope = A.scope_contract(
        tmp_path, bundle["bundle_sha256"], "samsung|REGULAR|ALL", "SOR", cache={}
    )
    aggregate = R.Aggregator()
    for value in (0.5, 1, 2, 3):
        r = row(identity=str(value), value=value)
        r.update(
            auxiliary_verdict="not_called",
            auxiliary_hash=None,
            **{
                k: v
                for k, v in scope.items()
                if k not in {"machine_component_sha256", "auxiliary_component_sha256"}
            },
        )
        r["scope_key"] = R.scope_key(r)
        aggregate.add(r)
    frozen = R.freeze_candidates(aggregate.daily(DAY), "frozen")
    aggregate.close()
    declared = next(iter(frozen["scopes"].values()))
    assert (
        declared["machine_status"] == "supported"
        and 0 < len(declared["candidates"]) <= 6
    )
    assert all(
        c["definition"]["kind"] == "machine_confirmation_filter_cf"
        for c in declared["candidates"]
    )


def test_inactive_overlay_does_not_require_overlay_feature():
    r = row()
    r["features"] = {}
    c = registry(r)["scopes"][r["scope_key"]]["candidates"][0]
    assert R.selection(r, c, dict(grade="B", state="RECOVERY")) is True


def test_parent_pointer_change_defers_even_if_scoped_definition_matches(
    tmp_path, monkeypatch
):
    from src.engine.scalping import mechanistic_entry_runtime_policy as P

    bundle, _ = source_bundle(tmp_path)
    scope = A.scope_contract(
        tmp_path, bundle["bundle_sha256"], "samsung|REGULAR|ALL", "SOR", cache={}
    )
    d = dict(kind="machine_confirmation_filter_cf", **scope)
    pointer = tmp_path / "runtime/mechanistic_entry_policy/current.json"
    A.atomic(pointer, dict(version=1))

    def changed(**kwargs):
        A.atomic(pointer, dict(version=2))
        return bundle

    monkeypatch.setattr(P, "load_effective", changed)
    assert not N.current_parent_matches(tmp_path, dict(definition=d))


def test_repaired_history_does_not_become_prospective(tmp_path, monkeypatch):
    from src.tests.test_main_market_weakness_research_automation import setup_sources

    data, _, _ = setup_sources(tmp_path, monkeypatch)
    A.process_date(data, DAY, stop_at=time.monotonic() + 5)
    cursor = A.read_json(A.namespace(data) / DAY / "cursor.json")
    # Outcome-independent fixture census supplies a candidate seed. A newer
    # retained, not yet processed date still belongs to the historical cutoff.
    a = R.Aggregator()
    a.add(row())
    daily = a.daily(DAY)
    a.close()
    A.atomic(cursor["daily_path"], daily)
    terminal = A.read_json(cursor["terminal_path"])
    A.atomic(
        cursor["terminal_path"],
        R.seal(dict(terminal, daily_sha256=daily["artifact_content_sha256"])),
    )
    future = data / "ai_decision_trace/ai_decision_trace_2026-10-12.jsonl"
    future.write_text("{}\n")
    A.cumulative(data, stop_at=time.monotonic() + 5)
    frozen = A.read_json(A.namespace(data) / "fixed_candidates.json")
    assert all(
        s["fixed_after_source_date"] >= "2026-10-12" for s in frozen["scopes"].values()
    )


def test_exact_auxiliary_request_normalizes_component_to_scoped_binding():
    body, t = native_capture()
    request = dict(
        input={"schema": "original_input"},
        prompt="original prompt",
        response_schema={"type": "object"},
    )
    body["source"]["auxiliary_request"] = request
    native = body["runtime_consumption"]["continuous_reversal"]
    native.update(
        auxiliary_component_sha256="a" * 64,
        **{
            field: R.digest(request[key])
            for key, field in (
                ("input", "input_sha256"),
                ("prompt", "prompt_sha256"),
                ("response_schema", "response_schema_sha256"),
            )
        },
    )
    rehash_native(body)
    t.update(
        continuous_reversal_consumption=native,
        machine_observation_sha256=body["machine_observation_sha256"],
    )
    projected = R.project_trace(t, DAY, "KOSPI")[0]
    projected.update(
        auxiliary_hash="a" * 64,
        auxiliary_version="original_version",
        auxiliary_verdict="PASS",
    )
    observation = R.project_native_observation(body, DAY)[0]
    assert observation["request_binding_verified"]
    observation["auxiliary_binding"] = dict(
        prompt_version="original_version", arm="one"
    )
    observation["cohort_contract"] = dict(verified=True)
    R.bind_native(projected, observation)
    assert projected["original_auxiliary_component_sha256"] == "a" * 64
    assert projected["auxiliary_hash"] == R.digest(observation["auxiliary_binding"])
    assert projected["auxiliary_binding_status"] == "verified"
    wrong = dict(projected, auxiliary_hash="other")
    R.bind_native(wrong, observation)
    assert (
        wrong["auxiliary_binding_status"] == "request_or_component_binding_unverified"
    )
    candidate = registry(row())["scopes"][row()["scope_key"]]["candidates"][0]
    assert (
        R.selection(
            wrong, candidate, dict(grade="B", state="WEAKNESS", index_change_pct=-2)
        )
        is None
    )


def test_missing_or_previous_phase_cannot_hide_daily_commit(tmp_path):
    assert A.unfinished_phase(tmp_path, DAY, dict(generation="new"))
    A.phase_receipt(tmp_path, DAY, "old", "completed")
    assert A.unfinished_phase(tmp_path, DAY, dict(generation="new"))


def test_gzip_alias_mismatch_is_a_source_gap(tmp_path, monkeypatch):
    from src.tests.test_main_market_weakness_research_automation import setup_sources

    data, p, _ = setup_sources(tmp_path, monkeypatch)
    write_gzip(Path(str(p) + ".gz"), b"{}\n")
    A.process_date(data, DAY, stop_at=time.monotonic() + 5)
    cursor = A.read_json(A.namespace(data) / DAY / "cursor.json")
    assert A.read_json(cursor["daily_path"])["census"].get("projected_rows", 0) == 0
    assert cursor["gaps"]["source_contract_invalid_or_unavailable"] == 1


def test_new_policy_dependency_creates_a_new_generation(tmp_path, monkeypatch):
    from src.tests.test_main_market_weakness_research_automation import setup_sources

    data, _, _ = setup_sources(tmp_path, monkeypatch)
    A.process_date(data, DAY, stop_at=time.monotonic() + 5)
    p = A.namespace(data) / DAY / "cursor.json"
    cursor = A.read_json(p)
    dependency = data / "runtime/mechanistic_entry_policy/generations/fixture.json"
    A.atomic(dependency, dict(value=1))
    cursor["source_dependency_receipts"] = [A.stat_receipt(dependency)]
    A.atomic(p, cursor)
    A.atomic(dependency, dict(value=2))
    result = A.process_date(data, DAY, stop_at=time.monotonic() + 5)
    assert result["delta"] == 1 and result["generation"] != cursor["generation"]


def test_replay_projection_binds_scope_and_separates_replay_kernel(
    tmp_path, monkeypatch
):
    bundle, _ = source_bundle(tmp_path)
    body, _ = native_capture()
    event = body["source"]["assessment"]["event"]
    record = dict(
        day=DAY,
        symbol=event["symbol"],
        scope="samsung|REGULAR|ALL|SOR",
        opportunity_key="canonical",
        native_alias=event["canonical_opportunity_id"],
        snapshot_obj=2,
        outcome=dict(status="WIN", delay_sec=10),
    )
    normalized = tmp_path / "normalized.json"
    normalized.write_text("verified source")
    report = R.seal(
        dict(
            schema="continuous_reversal_operating_comparison_v1",
            status="completed",
            source_date=DAY,
            label_contract=R.LABEL,
            parent_bundle_sha256=bundle["bundle_sha256"],
            execution_code_sha256="c" * 64,
            cells=[
                dict(
                    key="samsung|REGULAR|ALL",
                    **bundle["continuous_reversal"]["machine_cells"][
                        "samsung|REGULAR|ALL"
                    ],
                )
            ],
            partitions=[
                dict(
                    normalized_source=dict(
                        day=DAY, path=str(normalized), sha256=A.file_hash(normalized)
                    ),
                    records_object=1,
                    records_sha256=R.digest([record]),
                )
            ],
        )
    )
    p = tmp_path / "comparison.json"
    A.atomic(p, report)

    class Reader:
        receipts = {}

        def __init__(self, *a):
            pass

        def get(self, oid):
            return [record] if oid == 1 else [event, None]

        def close(self):
            pass

    monkeypatch.setattr(A, "ReadObjects", Reader)
    chunks = list(
        A.replay_records(
            tmp_path,
            DAY,
            A.stat_receipt(p),
            lambda _: "KOSPI",
            stop_at=time.monotonic() + 5,
        )
    )
    projected = chunks[0][0][0]
    assert projected["outcome"] == "W" and projected["auxiliary_hash"] is None
    assert projected["cohort_contract"]["verified"] and projected["machine_axes"]
    assert projected["cohort_contract"]["replay_kernel_sha256"] == "c" * 64
    assert projected["native_policy_ref"]["path"].endswith(
        bundle["bundle_sha256"] + ".json"
    )


def test_scoped_winner_group_does_not_change_for_publication_identity():
    a = R.Aggregator(registry(row()))
    favorable(a)
    c = copy.deepcopy(a.comparison("g")["comparisons"][0])
    a.close()
    c["definition"].update(
        scope_parent_machine_payload_sha256="scoped",
        auxiliary_binding={"prompt": "same"},
    )
    other = copy.deepcopy(c)
    other.update(scope_key="new-publication", winner_group="new-publication")
    other["scope"].update(machine_hash="new", auxiliary_hash="new")
    other["definition"].update(parent_hash="new", auxiliary_hash="new", after=2)
    assert N.winner_group(c) == N.winner_group(other)
    other["definition"]["kind"] = "machine_confirmation_filter_cf"
    assert N.winner_group(c) != N.winner_group(other)


def test_leave_cluster_retains_added_and_neither_masks():
    first = dict(
        selected=dict(W=2, F=2), excluded={}, added=dict(W=3), neither=dict(U=4)
    )
    second = dict(
        selected=dict(W=1, F=2), excluded={}, added=dict(F=2), neither=dict(W=1)
    )
    remainder = R.subtract_pairs(R.merge_pairs([first, second]), first)
    assert remainder["added"]["F"] == 2 and remainder["neither"]["W"] == 1
    assert R.pair_delta(remainder) == R.pair_delta(second)
    assert R.pair_delta(dict(second, neither=dict(W=999))) == R.pair_delta(second)


def test_unsupported_replay_boolean_is_never_selection_or_advisory():
    from src.tests.test_main_market_weakness_research_notify import comparison

    candidate = comparison()["comparisons"][0]
    candidate["definition"]["kind"] = "machine_confirmation_replay_cf"
    r = row()
    r["replay_selection"] = dict(
        verified=True,
        definition_sha256=R.digest(candidate["definition"]),
        baseline_selected=False,
        candidate_selected=True,
    )
    assert R.selection(r, candidate, r["joins"]["0"]) is None
    assert not N.advisory_eligible(candidate)


def test_post_auxiliary_filter_cannot_publish_added_population():
    from src.tests.test_main_market_weakness_research_notify import comparison

    candidate = comparison()["comparisons"][0]
    candidate["added_opportunities"] = 1
    assert not N.advisory_eligible(candidate)


def test_in_progress_date_defers_reconciliation_and_invalidates_old_comparison(
    tmp_path, monkeypatch
):
    from src.tests.test_main_market_weakness_research_automation import setup_sources
    from src.tests.test_main_market_weakness_research_notify import call, comparison

    data, _, _ = setup_sources(tmp_path, monkeypatch)
    root = A.namespace(data)
    A.process_date(data, DAY, stop_at=time.monotonic() + 5)
    complete = A.cumulative(data, stop_at=time.monotonic() + 5)
    call(root, comparison())  # Fixture transport only, durable sent receipt.
    state = (root / "outbox/state.json").read_bytes()
    cursor_path = root / DAY / "cursor.json"
    cursor = A.read_json(cursor_path)
    cursor.update(status="in_progress", generation="repair-in-progress")
    A.atomic(cursor_path, cursor)
    assert not A.comparison_current(data, complete)
    pending = A.cumulative(data, stop_at=time.monotonic() + 5)
    assert pending["pending_source_dates"] == [DAY]
    result = N.reconcile(root, pending)
    assert result["status"] == "deferred_migration_or_comparison"
    assert (root / "outbox/state.json").read_bytes() == state


def test_new_pending_date_invalidates_previously_complete_comparison(
    tmp_path, monkeypatch
):
    from src.tests.test_main_market_weakness_research_automation import setup_sources

    data, _, _ = setup_sources(tmp_path, monkeypatch)
    A.process_date(data, DAY, stop_at=time.monotonic() + 5)
    complete = A.cumulative(data, stop_at=time.monotonic() + 5)
    assert A.comparison_current(data, complete)
    A.atomic(
        A.namespace(data) / "2026-10-09/cursor.json",
        dict(source_date="2026-10-09", generation="new", status="in_progress"),
    )
    assert not A.comparison_current(data, complete)


def test_comparison_checkpoint_includes_conflicting_scope(tmp_path, monkeypatch):
    from src.tests.test_main_market_weakness_research_automation import setup_sources

    data, _, _ = setup_sources(tmp_path, monkeypatch)
    root = A.namespace(data)
    A.process_date(data, DAY, stop_at=time.monotonic() + 5)
    cursor = A.read_json(root / DAY / "cursor.json")
    fixed = R.seal(dict(registry(row()), repair_version=R.REPAIR_VERSION))
    A.atomic(root / "fixed_candidates.json", fixed)
    a = R.Aggregator(fixed)
    favorable(a)
    daily = a.daily(DAY)
    aggregate = a.export()
    a.close()
    sid = next(iter(fixed["scopes"]))

    def install(conflicted):
        changed = R.seal(dict(daily, conflict_scopes=[sid] if conflicted else []))
        A.atomic(cursor["daily_path"], changed)
        terminal = A.read_json(cursor["terminal_path"])
        A.atomic(
            cursor["terminal_path"],
            R.seal(dict(terminal, daily_sha256=changed["artifact_content_sha256"])),
        )
        cache_key = R.digest(
            [changed["artifact_content_sha256"], fixed["scopes"], A.code_hash()]
        )
        A.atomic(
            root / "aggregate_cache" / (cache_key + ".json"),
            R.seal(dict(aggregate, conflict_scopes=[sid] if conflicted else [])),
        )

    install(False)
    first = A.cumulative(data, stop_at=time.monotonic() + 5)
    assert first["comparisons"][0]["status"] == "eligible_advisory"
    install(True)
    second = A.cumulative(data, stop_at=time.monotonic() + 5)
    assert second["comparisons"][0]["status"] == "source_gap"
    assert second["comparisons"][0]["scope_winner"] is False


@pytest.mark.parametrize("replacement", ["new_winner", "source_gap"])
def test_pending_withdrawal_reconciles_against_current_transition(
    tmp_path, replacement
):
    from src.tests.test_main_market_weakness_research_notify import (
        call,
        comparison,
        invoke,
    )

    original = comparison()
    call(tmp_path, original)
    weak = copy.deepcopy(original)
    weak["comparisons"][0].update(status="hold_observation", scope_winner=False)
    invoke(
        tmp_path, R.seal(weak), lambda _: pytest.fail("deferred"), gate=lambda: False
    )
    changed = copy.deepcopy(original)
    candidate = changed["comparisons"][0]
    if replacement == "new_winner":
        candidate["definition"].update(after=0.8, feature_max_exclusive=0.8)
    else:
        candidate.update(status="source_gap", scope_winner=False)
    messages = []
    invoke(
        tmp_path,
        R.seal(changed),
        lambda m: messages.append(m) or dict(status="sent", message_id=2),
    )
    assert len(messages) == 1
    assert "추천 철회" not in messages[0]
    assert (
        "이전 안내를 이 후보로 대체" if replacement == "new_winner" else "오류 정정"
    ) in messages[0]


def test_cumulative_recovers_comparison_committed_before_manifest(
    tmp_path, monkeypatch
):
    from src.tests.test_main_market_weakness_research_automation import setup_sources

    data, _, _ = setup_sources(tmp_path, monkeypatch)
    A.process_date(data, DAY, stop_at=time.monotonic() + 5)
    original = A.atomic

    def crash(path, value, **kwargs):
        if Path(path).name == "manifest.json":
            raise OSError("crash before manifest")
        return original(path, value, **kwargs)

    monkeypatch.setattr(A, "atomic", crash)
    with pytest.raises(OSError, match="crash before manifest"):
        A.cumulative(data, stop_at=time.monotonic() + 5)
    monkeypatch.setattr(A, "atomic", original)
    monkeypatch.setattr(
        R.Aggregator, "comparison", lambda *a, **kw: pytest.fail("comparison repeated")
    )
    result = A.cumulative(data, stop_at=time.monotonic() + 5)
    assert A.comparison_current(data, result)
    current = A.read_json(A.namespace(data) / "cumulative/current.json")
    assert current["candidate_sha256"] == result["artifact_content_sha256"]


def test_projection_write_failure_does_not_skip_source_as_gap(tmp_path, monkeypatch):
    from src.tests.test_main_market_weakness_research_automation import setup_sources

    data, _, _ = setup_sources(tmp_path, monkeypatch)
    original = A.write_partition
    monkeypatch.setattr(
        A,
        "write_partition",
        lambda *a: (_ for _ in ()).throw(OSError("destination unavailable")),
    )
    with pytest.raises(A.Deferred, match="projection_commit_failed"):
        A.process_date(data, DAY, stop_at=time.monotonic() + 5)
    monkeypatch.setattr(A, "write_partition", original)
    A.process_date(data, DAY, stop_at=time.monotonic() + 5)
    cursor = A.read_json(A.namespace(data) / DAY / "cursor.json")
    daily = A.read_json(cursor["daily_path"])
    assert daily["census"]["projected_rows"] == 1
    assert "source_contract_invalid_or_unavailable" not in cursor["gaps"]


@pytest.mark.parametrize(
    "value,reason", [(None, "feature_missing"), (0.1, "no_tightening_cutpoint")]
)
def test_verified_axis_without_candidate_keeps_actual_capability_reason(
    tmp_path, value, reason
):
    bundle, _ = source_bundle(tmp_path)
    scope = A.scope_contract(
        tmp_path, bundle["bundle_sha256"], "samsung|REGULAR|ALL", "SOR", cache={}
    )
    r = row(value=value)
    r.update(machine_axes=scope["machine_axes"], auxiliary_hash=None)
    r["scope_key"] = R.scope_key(r)
    a = R.Aggregator()
    a.add(r)
    frozen = R.freeze_candidates(a.daily(DAY), "g")
    assert frozen["scopes"][r["scope_key"]]["machine_reason"] == reason
    assert a.comparison("g")["capability_by_scope"][r["scope_key"]]["machine"] == reason
    a.close()


def test_source_rotation_precedes_notification_waiters_and_survives_nights(
    tmp_path, monkeypatch
):
    days = [
        "2026-09-29",
        "2026-09-30",
        "2026-10-02",
        "2026-10-06",
        "2026-10-07",
        "2026-10-08",
        "2026-10-12",
        "2026-10-13",
        "2026-10-14",
    ]
    root = A.namespace(tmp_path)
    for day in days:
        A.atomic(root / day / "cursor.json", dict(source_date=day, status="completed"))
    current = {days[0], days[-1]}
    monkeypatch.setattr(A, "cursor_current", lambda _, c: c["source_date"] in current)
    monkeypatch.setattr(A, "unfinished_phase", lambda *a: True)
    selected = []
    for _ in range(2):
        for night in ("2026-10-14", "2026-10-15"):
            selected.extend(
                A.select_source_date(
                    tmp_path, days, night=night, check_preflight=lambda: None
                )
                for _ in range(4)
            )
    # Even permanently failing repairs are visited fairly, without a midnight reset.
    assert selected[:14] == days[1:-1] * 2
    current.update(days)
    assert [
        A.select_source_date(
            tmp_path, days, night="2026-10-15", check_preflight=lambda: None
        )
        for _ in days
    ] == days


def test_source_rotation_skips_open_next_day_and_has_no_outside_budget_write(tmp_path):
    root = A.namespace(tmp_path)
    assert (
        A.select_source_date(
            tmp_path, ["2026-10-15"], night="2026-10-14", check_preflight=lambda: None
        )
        is None
    )
    assert not root.exists()

    def expired():
        raise A.Deferred("budget_expired")

    with pytest.raises(A.Deferred, match="budget_expired"):
        A.select_source_date(tmp_path, [DAY], night=DAY, check_preflight=expired)
    assert not root.exists()


def test_missing_retained_day_is_discovered_and_closes_as_gap(tmp_path, monkeypatch):
    root = A.namespace(tmp_path)
    A.atomic(root / DAY / "cursor.json", dict(source_date=DAY, status="completed"))
    assert DAY in A.discover_dates(tmp_path, dict(evidence_start_date="2026-09-29"))
    monkeypatch.setattr(A, "listing_lookup", lambda *a: (lambda _: "KOSPI", None))
    result = A.process_date(tmp_path, DAY, stop_at=time.monotonic() + 5)
    cursor = A.read_json(root / DAY / "cursor.json")
    assert result["status"] == "completed_with_source_gaps"
    assert cursor["gaps"]["retained_decision_sources_unavailable"] == 1
    assert A.cursor_current(tmp_path, cursor)
    assert not A.cumulative(tmp_path, stop_at=time.monotonic() + 5)["migration_pending"]


def test_outside_night_window_never_advances_source_rotation(tmp_path, monkeypatch):
    root = A.namespace(tmp_path)
    A.atomic(root / "installation.json", R.seal(dict(enabled=True)))
    path = root / "schedule_cursor.json"
    A.atomic(path, R.seal(dict(last_source_date=DAY)))
    before = path.read_bytes(), path.stat().st_mtime_ns
    monkeypatch.setattr(A, "verify_installed_calendar", lambda _: True)
    monkeypatch.setattr(
        A, "night_window", lambda *a: (None, None, "outside_night_window")
    )
    monkeypatch.setattr(
        A, "discover_dates", lambda *a: pytest.fail("intraday discovery")
    )
    assert A.scheduled(tmp_path)["reason"] == "outside_night_window"
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before


def observer_state_fixture(data, obs):
    state = dict(
        market_weakness=dict(
            last_source_gate=dict(passed=True),
            last_observation_id=obs["observation_id"],
            last_observation_as_of=obs["as_of"],
            market_states=dict(KOSPI=dict(active=True)),
        ),
        market_weakness_observer_health=dict(
            ready=True,
            checked_at_ts=datetime.fromisoformat(obs["as_of"]).timestamp() + 1,
            last_healthy_observation_id=obs["observation_id"],
        ),
    )
    path = data.parent / "tmp/market_weakness_observer_state.json"
    A.atomic(path, state)
    return path


def test_frozen_observer_evidence_survives_live_advance_and_preserves_raw_bytes(
    tmp_path, monkeypatch
):
    from src.tests.test_main_market_weakness_research_automation import setup_sources

    data, _, obs_path = setup_sources(tmp_path, monkeypatch)
    state_path = observer_state_fixture(data, A.read_json(obs_path))
    original = state_path.read_bytes()
    first = A.process_date(data, DAY, stop_at=time.monotonic() + 5)
    cursor = A.read_json(A.namespace(data) / DAY / "cursor.json")
    receipt = cursor["source_descriptor"]["observer_snapshot"]
    snapshot = A.check_seal(A.read_json(receipt["path"]))
    assert snapshot["source_raw"].encode() == original
    assert snapshot["source_sha256"] == hashlib.sha256(original).hexdigest()
    assert str(state_path) not in {
        r["path"] for r in cursor["source_descriptor"]["observations"]
    }
    A.atomic(state_path, dict(new_day="2026-10-09"))
    assert A.cursor_current(data, cursor)
    second = A.process_date(data, DAY, stop_at=time.monotonic() + 5)
    assert second["delta"] == 0 and second["generation"] == first["generation"]
    obs, _, _ = A.observations(data, DAY, observer_snapshot=receipt)
    assert obs[0]["availability_receipt_verified"] is True
    # Retained market-source edits still invalidate the day independently.
    A.atomic(obs_path, observation(DAY + "T09:01:00+09:00"))
    assert not A.cursor_current(data, cursor)
    assert (
        A.process_date(data, DAY, stop_at=time.monotonic() + 5)["generation"]
        != first["generation"]
    )


@pytest.mark.parametrize("mutation", ["corrupt", "remove", "outside_namespace"])
def test_frozen_observer_corruption_never_falls_back_to_live(tmp_path, mutation):
    data = tmp_path / "data"
    obs = observation()
    A.atomic(data / "report/market_weakness_observations" / DAY / "one.json", obs)
    observer_state_fixture(data, obs)
    _, receipts, _ = A.observations(data, DAY)
    receipt = receipts[-1]
    path = Path(receipt["path"])
    if mutation == "remove":
        path.unlink()
    elif mutation == "corrupt":
        A.atomic(path, {"invalid": True})
    else:
        receipt = A.stat_receipt(
            data.parent / "tmp/market_weakness_observer_state.json"
        )
    with pytest.raises(ValueError, match="observer_snapshot_receipt_invalid"):
        A.observations(data, DAY, observer_snapshot=receipt)


def test_archive_rejection_precedes_observer_capture(tmp_path, monkeypatch):
    monkeypatch.setattr(
        A, "observations", lambda *a, **k: pytest.fail("archive capture")
    )
    with pytest.raises(ValueError, match="archive_date_forbidden"):
        A.process_date(tmp_path, "2026-09-28", stop_at=time.monotonic() + 5)
    assert not A.namespace(tmp_path).exists()


@pytest.mark.parametrize(
    "field,value",
    [("source_raw", None), ("source_path", "/unrelated"), ("runtime_effect", True)],
)
def test_frozen_observer_contract_damage_is_explicit(tmp_path, field, value):
    data = tmp_path / "data"
    obs = observation()
    A.atomic(data / "report/market_weakness_observations" / DAY / "one.json", obs)
    observer_state_fixture(data, obs)
    _, receipts, _ = A.observations(data, DAY)
    path = Path(receipts[-1]["path"])
    snapshot = A.read_json(path)
    snapshot[field] = value
    A.atomic(path, R.seal(snapshot))
    with pytest.raises(ValueError, match="observer_snapshot_contract_invalid"):
        A.observations(data, DAY, observer_snapshot=A.stat_receipt(path))


@pytest.mark.parametrize("mode", ["missing", "resolved", "mixed"])
def test_retained_replay_label_chain_reports_epoch_gap_without_inventing_outcome(
    tmp_path, monkeypatch, mode
):
    resolved = mode != "missing"
    data = tmp_path / "data"
    bundle, _ = source_bundle(data)
    body, t = native_capture()
    event = body["source"]["assessment"]["event"]
    records = (
        [
            dict(
                day=DAY,
                symbol=event["symbol"],
                scope="samsung|REGULAR|ALL|SOR",
                opportunity_key="canonical",
                native_alias="canonical",
                snapshot_obj=2,
                outcome=dict(status="WIN", delay_sec=10),
            )
        ]
        if resolved
        else []
    )
    normalized = data / "normalized.json"
    normalized.write_text("retained source")
    report = R.seal(
        dict(
            schema="continuous_reversal_operating_comparison_v1",
            source_date=DAY,
            status="completed",
            label_contract=R.LABEL,
            parent_bundle_sha256=bundle["bundle_sha256"],
            partitions=[
                dict(
                    normalized_source=dict(
                        day=DAY,
                        path=str(normalized),
                        sha256=A.file_hash(normalized),
                        issues={} if resolved else dict(source_epoch_unverified=25),
                    ),
                    records_object=1,
                    records_sha256=R.digest(records),
                )
            ],
        )
    )
    if mode == "mixed":
        report["partitions"].append(
            dict(
                normalized_source=dict(
                    day=DAY,
                    path=str(normalized),
                    sha256=A.file_hash(normalized),
                    issues=dict(source_epoch_unverified=25),
                ),
                records_object=3,
                records_sha256=R.digest([]),
            )
        )
        report = R.seal(report)
    A.atomic(
        data / "report/continuous_reversal_operating" / DAY / "machine-comparison.json",
        report,
    )

    class Reader:
        receipts = {}

        def __init__(self, *a):
            pass

        def get(self, oid):
            if oid == 3:
                return []
            return records if oid == 1 else [event, None]

        def close(self):
            pass

    monkeypatch.setattr(A, "ReadObjects", Reader)
    monkeypatch.setattr(A, "listing_lookup", lambda *a: (lambda _: "KOSPI", None))
    write_gzip(
        data / "ai_decision_payloads" / f"ai_decision_payloads_{DAY}.jsonl.gz",
        (json.dumps(body) + "\n").encode(),
    )
    write_gzip(
        data / "ai_decision_trace" / f"ai_decision_trace_{DAY}.jsonl.gz",
        (json.dumps(t) + "\n").encode(),
    )
    A.process_date(data, DAY, stop_at=time.monotonic() + 5)
    cursor = A.read_json(A.namespace(data) / DAY / "cursor.json")
    daily = A.check_seal(A.read_json(cursor["daily_path"]))
    natural = [
        r
        for r in A.projection_rows(cursor["partitions"])
        if r["decision_origin"] != "confirmation_replay"
    ]
    assert len(natural) == 1 and natural[0]["outcome"] == ("W" if resolved else "U")
    if resolved:
        assert natural[0]["label_binding"] == "exact_event_time_actual_ask"
    if mode == "resolved":
        assert "replay_empty_partition" not in daily["input_exclusions"]
    else:
        assert daily["input_exclusions"]["replay_empty_partition"] == 1
        assert (
            daily["input_exclusions"]["replay_upstream_source_epoch_unverified"] == 25
        )
        terminal = A.check_seal(A.read_json(cursor["terminal_path"]))
        assert terminal["gaps"] == daily["input_exclusions"]
