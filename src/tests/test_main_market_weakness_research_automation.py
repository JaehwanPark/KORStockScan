import copy
from datetime import datetime, timedelta
import gzip
import json
from pathlib import Path
import sqlite3
import sys
import time
import zlib

import pytest
from src.engine.automation import main_market_weakness_research as A
from src.engine.scalping import market_weakness_research as R
from src.tests.test_main_market_weakness_research import DAY, observation, row, trace


def setup_sources(tmp_path, monkeypatch):
    data = tmp_path / "data"
    data.mkdir()
    p = data / "ai_decision_trace" / ("ai_decision_trace_" + DAY + ".jsonl")
    p.parent.mkdir()
    p.write_text(json.dumps(trace()) + "\n")
    obs = data / "report/market_weakness_observations" / DAY / "o.json"
    A.atomic(obs, observation())
    monkeypatch.setattr(A, "listing_lookup", lambda *a: (lambda _: "KOSPI", None))
    return data, p, obs


def run_date(data):
    return A.process_date(data, DAY, stop_at=time.monotonic() + 15)


def test_partition_before_cursor_and_unchanged_is_delta_zero(tmp_path, monkeypatch):
    data, p, obs = setup_sources(tmp_path, monkeypatch)
    result = run_date(data)
    cursor = A.read_json(A.namespace(data) / DAY / "cursor.json")
    assert result["delta"] == 1
    assert cursor["partitions"]
    assert A.cursor_current(data, cursor)
    daily = A.read_json(cursor["daily_path"])
    assert daily["census"]["attempt_machine_BLOCK"] == 1
    assert daily["census"]["attempt_auxiliary_not_called"] == 1
    assert next(iter(daily["scopes"].values()))["counts"]["outcome_U"] == 1
    assert run_date(data)["delta"] == 0
    assert Path(cursor["daily_path"]).with_suffix(".md").exists()
    manifest = A.read_json(cursor["manifest_path"])
    assert manifest["source_ranges"][0]["start"] == 0
    assert manifest["source_ranges"][0]["sha256"] == A.file_hash(p)


def test_tail_deferred_then_append_and_prefix_rewrite_get_new_generation(
    tmp_path, monkeypatch
):
    data, p, _ = setup_sources(tmp_path, monkeypatch)
    p.write_bytes(p.read_bytes() + b'{"partial":')
    with pytest.raises(A.Deferred, match="incomplete_source_tail"):
        run_date(data)
    c = A.read_json(A.namespace(data) / DAY / "cursor.json")
    assert c["status"] == "in_progress"
    assert not c.get("terminal_path")
    p.write_bytes(p.read_bytes() + b"true}\n")
    r = run_date(data)
    assert r["generation"] != c["generation"]
    content = p.read_bytes()
    p.write_bytes(content.replace(b"BLOCK", b"WAIT_"))
    assert run_date(data)["generation"] != r["generation"]


def test_crash_after_partition_does_not_advance_cursor(tmp_path, monkeypatch):
    data, _, _ = setup_sources(tmp_path, monkeypatch)
    original = A.atomic

    def crash(path, value, **kwargs):
        if Path(path).name == "cursor.json":
            raise OSError("simulated crash")
        original(path, value, **kwargs)

    monkeypatch.setattr(A, "atomic", crash)
    with pytest.raises(OSError):
        run_date(data)
    assert not (A.namespace(data) / DAY / "cursor.json").exists()
    monkeypatch.setattr(A, "atomic", original)
    assert run_date(data)["delta"] == 1
    assert len(list((A.namespace(data) / "objects").glob("*.json"))) == 1


@pytest.mark.parametrize(
    "mutation", ["observation", "add_observation", "remove_source"]
)
def test_cumulative_invalidates_changed_upstream(tmp_path, monkeypatch, mutation):
    data, p, o = setup_sources(tmp_path, monkeypatch)
    run_date(data)
    first = A.cumulative(data, stop_at=time.monotonic() + 15)
    if mutation == "observation":
        o.write_text("{}")
    elif mutation == "add_observation":
        A.atomic(o.with_name("other.json"), observation(DAY + "T09:01:00+09:00"))
    else:
        p.unlink()
    second = A.cumulative(data, stop_at=time.monotonic() + 15)
    assert second["generation"] != first["generation"]
    assert second["invalidated_source_dates"] == [DAY]
    assert not second["source_generations"]
    assert not A.comparison_current(data, first)


def test_cumulative_same_generation_reuses_compact_cache(tmp_path, monkeypatch):
    data, _, _ = setup_sources(tmp_path, monkeypatch)
    run_date(data)
    first = A.cumulative(data, stop_at=time.monotonic() + 15)
    monkeypatch.setattr(
        A,
        "projection_rows",
        lambda _: (_ for _ in ()).throw(AssertionError("no rescan")),
    )
    assert A.cumulative(data, stop_at=time.monotonic() + 15) == first


def test_archive_date_does_not_use_historical_policy_refresh_fallback(
    tmp_path, monkeypatch
):
    data, _, _ = setup_sources(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="archive_date_forbidden"):
        A.process_date(data, "2026-09-20", stop_at=time.monotonic() + 10)


def test_invalid_observation_is_identifiable_gap_not_global_crash(tmp_path):
    data = tmp_path / "data"
    p = data / "report/market_weakness_observations" / DAY / "bad.json"
    p.parent.mkdir(parents=True)
    p.write_text("{bad")
    obs, receipts, gaps = A.observations(data, DAY)
    assert obs == []
    assert len(receipts) == 1
    assert gaps["invalid_market_observation"] == 1


def test_source_supplied_availability_is_not_receipt_proof(tmp_path):
    data = tmp_path / "data"
    o = observation()
    o.update(
        availability_receipt_verified=True,
        observed_available_at=DAY + "T09:00:00+09:00",
    )
    A.atomic(data / "report/market_weakness_observations" / DAY / "o.json", o)
    obs, _, _ = A.observations(data, DAY)
    assert not obs[0].get("availability_receipt_verified")


def test_shared_objects_are_read_only_bounded_and_hash_verified(tmp_path):
    data = tmp_path / "data"
    root = data / "ai_comparison_store/v1"
    (root / "packs").mkdir(parents=True)
    db = sqlite3.connect(root / "metadata.sqlite3")
    db.execute(
        "CREATE TABLE objects(id INTEGER PRIMARY KEY,hash TEXT,pack TEXT,offset INTEGER,length INTEGER,size INTEGER)"
    )
    raw = b'{"small":true}'
    encoded = zlib.compress(raw)
    (root / "packs/a.pack").write_bytes(encoded)
    import hashlib

    db.execute(
        "INSERT INTO objects VALUES(1,?,?,?,?,?)",
        (hashlib.sha256(raw).hexdigest(), "a.pack", 0, len(encoded), len(raw)),
    )
    db.execute(
        "INSERT INTO objects VALUES(2,?,?,?,?,?)",
        ("wrong", "a.pack", 0, len(encoded), len(raw)),
    )
    db.execute(
        "INSERT INTO objects VALUES(3,?,?,?,?,?)", ("wrong", "../outside", 0, 1, 1)
    )
    db.commit()
    db.close()
    store = A.ReadObjects(data)
    assert store.get(1) == {"small": True}
    with pytest.raises(sqlite3.OperationalError):
        store.db.execute("DELETE FROM objects")
    with pytest.raises(ValueError, match="hash_or_size"):
        store.get(2)
    with pytest.raises(ValueError, match="size_or_path"):
        store.get(3)
    store.close()


def test_normalized_source_hash_must_match_and_removal_invalidates(tmp_path):
    p = tmp_path / "source"
    p.write_text("original")
    A.verify_file(tmp_path / "own", p, A.file_hash(p), stop_at=time.monotonic() + 1)
    with pytest.raises(ValueError):
        A.verify_file(tmp_path / "own", p, "wrong", stop_at=time.monotonic() + 1)
    p.unlink()
    with pytest.raises(FileNotFoundError):
        A.verify_file(tmp_path / "own", p, "wrong", stop_at=time.monotonic() + 1)


def test_natural_label_requires_same_typed_event_time_and_ask(tmp_path):
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE labels(id TEXT PRIMARY KEY,row TEXT,conflict INTEGER)")
    r = row(origin="confirmation_replay")
    r["auxiliary_hash"] = None
    r["canonical_alias"] = "alias"
    r["source_ref"] = {"report": "sealed"}
    A._index_label(db, r)
    n = row()
    n["opportunity_id"] = "alias"
    n["outcome"] = "U"
    A.bind_natural_label(n, db)
    assert n["outcome"] == "W"
    n["outcome"] = "U"
    n["entry_ask"] = 101
    A.bind_natural_label(n, db)
    assert n["outcome"] == "U"


def test_actual_auxiliary_export_requires_exact_ask_and_validator(tmp_path):
    from src.engine.scalping import reversal_operating_auxiliary as U
    from src.engine.scalping import reversal_path_auxiliary as V
    from src.engine.scalping import reversal_operating_evaluation as E

    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE labels(id TEXT PRIMARY KEY,row TEXT,conflict INTEGER)")
    r = row(origin="confirmation_replay")
    r["auxiliary_hash"] = None
    r["source_ref"] = {"report": "sealed"}
    A._index_label(db, r)
    context = dict(
        opportunity_key="one",
        as_of=r["machine_confirmed_at"],
        entry_ask=100,
        symbol=r["symbol"],
        venue="SOR",
        objective=dict(
            net_target_pct=0.4,
            net_soft_stop_pct=-3.0,
            cost_rate=0.0023,
            horizon_seconds=1800,
        ),
    )
    inp = dict(
        schema=U.VERSION,
        common_context=context,
        signals=[{"ref": "sig"}],
        observation_phase={"stage": "UNION"},
        entry_setup_evidence_v1=dict(
            positive_facts=[{"id": "observed_machine_signal"}],
            context_facts=[],
            contradicting_facts=[],
            risk_fact_bindings={},
        ),
    )
    response = dict(
        schema=U.VERSION,
        decision_scope="COMMON_OPPORTUNITY",
        assessed_signal_refs=["sig"],
        risk_verdict="PASS",
        risk_codes=["NO_BLOCKING_RISK"],
        supporting_fact_ids=["observed_machine_signal"],
        contradicting_fact_ids=[],
        confidence=50,
    )
    arm = V.V1.ARMS[0] if hasattr(V, "V1") else "reversal_context_v1"
    # Use the documented arm registry rather than mocking the response decoder.
    arm = U.V1.ARMS[0]
    assert not E.validate_response(response, inp, arm=arm)
    req = dict(
        candidate_input=inp,
        candidate_input_sha256=R.digest(inp),
        micro_reversion_replay_arm=arm,
        candidate=dict(
            system_prompt="actual prompt",
            prompt_version=U.VERSION + ":" + arm,
            response_schema_sha256="schema",
            provider="p",
            model="m",
        ),
        paired_replay_id="request",
        **R.AUTH,
    )
    entry = dict(
        request=req,
        request_identity="request",
        transport_invoked=True,
        validation_errors=[],
        result=dict(
            candidate_response=response, provider_provenance={"response_id": "actual"}
        ),
    )
    p = tmp_path / "export.jsonl.gz"
    with gzip.open(p, "wt") as f:
        f.write(json.dumps(entry) + "\n")
    source = dict(path=str(p), sha256=A.file_hash(p))
    rows, _, done, gaps = A.stored_auxiliary_records(source, DAY, db)
    assert done and not gaps
    assert rows[0]["auxiliary_verdict"] == "PASS"
    assert rows[0]["response_origin"] == "stored_offline_actual"
    inp["common_context"]["entry_ask"] = 101
    req["candidate_input_sha256"] = R.digest(inp)
    with gzip.open(p, "wt") as f:
        f.write(json.dumps(entry) + "\n")
    assert not A.stored_auxiliary_records(source, DAY, db)[0]


@pytest.mark.parametrize(
    "at,night,reason",
    [
        ("2026-10-08T21:40:00+09:00", "2026-10-08", None),
        ("2026-10-09T05:40:00+09:00", "2026-10-08", None),
        ("2026-10-09T06:30:00+09:00", None, "outside_night_window"),
        ("2026-10-08T19:00:00+09:00", None, "outside_night_window"),
    ],
)
def test_night_identity_and_closed_session(at, night, reason):
    cfg = dict(calendar_verified=True, next_main_preparation_clock_kst="07:35")
    n, d, r = A.night_window(datetime.fromisoformat(at), cfg)
    assert (n, r) == (night, reason)


def test_unverified_calendar_and_earlier_main_preparation_fail_closed():
    at = datetime.fromisoformat("2026-10-09T05:40:00+09:00")
    assert A.night_window(at, {})[2] == "main_preparation_calendar_unverified"
    assert (
        A.night_window(
            at, dict(calendar_verified=True, next_main_preparation_clock_kst="05:00")
        )[2]
        == "market_open_or_main_preparation_due"
    )


@pytest.mark.parametrize(
    "zone,hour,hours", [("UTC", "22", "12-20"), ("Asia/Seoul", "7", "0-5,21-23")]
)
def test_optional_cron_preserves_all_other_owners(zone, hour, hours, tmp_path):
    original = f"35 {hour} * * 1-5 bash /preopen # THRESHOLD_CYCLE_PREOPEN\n0 12 * * * bash /eod # EOD\n"
    new = A.render_optional_cron(original, tmp_path, zone)
    assert original in new
    assert f"40 {hours}" in new
    assert new.count(A.TAG) == 1
    assert A.render_optional_cron(new, tmp_path, zone) == new


def test_disabled_schedule_reads_no_sources(tmp_path, monkeypatch):
    monkeypatch.setattr(A, "source_plan", lambda *a: pytest.fail("heavy source read"))
    assert A.scheduled(tmp_path)["status"] == "disabled_or_not_installed"


def test_worker_cli_cannot_bypass_supervisor(tmp_path, capsys):
    data = tmp_path / "data"
    A.atomic(
        A.namespace(data) / "installation.json", R.seal(dict(enabled=True, **R.AUTH))
    )
    assert A.main(["--data-root", str(data), "--worker-date", DAY]) == 0
    assert "supervisor_reservation_required" in capsys.readouterr().out


def test_supervisor_terminates_group_on_wall_or_memory():
    result = A.supervise(
        [sys.executable, "-c", "import time;time.sleep(30)"],
        seconds=0.05,
        gate=lambda: True,
    )
    assert result["reason"] == "worker_wall_budget"
    assert result["exit_code"] != 0
    result = A.supervise(
        [sys.executable, "-c", "import time;time.sleep(30)"],
        seconds=1,
        gate=lambda: True,
        rss=lambda _: 10**9,
    )
    assert result["reason"] == "worker_process_group_memory_limit"


def test_heavy_owner_probe_matches_tokens_not_unrelated_command_text(tmp_path):
    p = tmp_path / "123/cmdline"
    p.parent.mkdir()
    p.write_bytes(b'python\0-c\0print("run_threshold_cycle_postclose.sh")\0')
    assert not A.heavy_owner_running(tmp_path)
    p.write_bytes(b"bash\0/work/run_threshold_cycle_postclose.sh\0")
    assert A.heavy_owner_running(tmp_path)


def test_namespace_lock_never_waits(tmp_path):
    with A.lock(tmp_path / "lock"):
        with pytest.raises(A.Deferred, match="namespace_busy"):
            with A.lock(tmp_path / "lock"):
                pass


def test_optional_worker_never_added_to_required_or_live_consumers():
    root = Path(__file__).resolve().parents[2]
    for name in (
        "src/engine/infrastructure/runtime_release_router.py",
        "src/engine/automation/postclose_summary_handoff.py",
        "src/engine/bot.py",
    ):
        p = root / name
        if p.exists():
            assert A.MODULE not in p.read_text()
    script = (root / "deploy/install_stage2_ops_cron.sh").read_text()
    assert script.index("--market-weakness-research-only") < script.index("TMP_CRON=")


def test_earlier_preparation_removes_late_cron_slots(tmp_path):
    original = "20 5 * * * bash /preopen # THRESHOLD_CYCLE_PREOPEN\n"
    output = A.render_optional_cron(original, tmp_path, "Asia/Seoul")
    assert "40 0-4,21-23" in output
    assert A.night_window(
        datetime.fromisoformat("2026-10-09T05:40:00+09:00"),
        dict(calendar_verified=True, next_main_preparation_clock_kst="05:20"),
    )[2]


def test_night_reservations_survive_failures_and_do_not_reset_at_midnight(
    tmp_path, monkeypatch
):
    class Clock(datetime):
        current = datetime.fromisoformat("2026-10-08T23:40:00+09:00")

        @classmethod
        def now(cls, tz=None):
            return cls.current

    monkeypatch.setattr(A, "datetime", Clock)
    monkeypatch.setattr(A, "verify_installed_calendar", lambda _: True)
    monkeypatch.setattr(A, "heavy_owner_running", lambda: False)
    monkeypatch.setattr(A, "discover_dates", lambda *a: [DAY])
    monkeypatch.setattr(
        A,
        "supervise",
        lambda *a, **k: dict(exit_code=1, reason=None, wall_seconds=0.01),
    )
    cfg = R.seal(
        dict(
            enabled=True,
            calendar_verified=True,
            next_main_preparation_clock_kst="07:35",
            evidence_start_date="2026-09-29",
        )
    )
    A.atomic(A.namespace(tmp_path) / "installation.json", cfg)
    assert A.scheduled(tmp_path)["status"] == "failed_contract"
    Clock.current = datetime.fromisoformat("2026-10-09T00:40:00+09:00")
    assert A.scheduled(tmp_path)["night_id"] == "2026-10-08"
    state = A.read_json(A.namespace(tmp_path) / "nights/2026-10-08.json")
    assert state["attempts"] == 2
    assert state["reserved_seconds"] == 120
    for _ in range(7):
        A.scheduled(tmp_path)
    assert A.scheduled(tmp_path)["reason"] == "night_budget_exhausted"
    state = A.read_json(A.namespace(tmp_path) / "nights/2026-10-08.json")
    assert state["attempts"] == 9
    assert state["reserved_seconds"] == 540


def test_deferred_worker_exit_zero_is_not_completed(tmp_path, monkeypatch):
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.fromisoformat("2026-10-08T22:40:00+09:00")

    monkeypatch.setattr(A, "datetime", Clock)
    monkeypatch.setattr(A, "verify_installed_calendar", lambda _: True)
    monkeypatch.setattr(A, "heavy_owner_running", lambda: False)
    monkeypatch.setattr(A, "discover_dates", lambda *a: [DAY])
    A.atomic(
        A.namespace(tmp_path) / "installation.json",
        R.seal(
            dict(
                enabled=True,
                calendar_verified=True,
                next_main_preparation_clock_kst="07:35",
            )
        ),
    )

    def supervise(command, **kwargs):
        ident = command[command.index("--reservation-id") + 1]
        p = A.namespace(tmp_path) / "attempts" / (ident + ".json")
        t = A.read_json(p)
        A.atomic(p, dict(t, status="deferred_resource_or_window"))
        return dict(exit_code=0, reason=None, wall_seconds=0.01)

    monkeypatch.setattr(A, "supervise", supervise)
    assert A.scheduled(tmp_path)["status"] == "deferred_resource_or_window"


@pytest.mark.parametrize(
    "limit,reason",
    [
        ("wall", "supervisor_preflight_wall_budget"),
        ("memory", "supervisor_preflight_memory_limit"),
        ("window", "supervisor_preflight_window_or_resource_changed"),
        ("owner", "supervisor_preflight_window_or_resource_changed"),
    ],
)
def test_source_selection_limits_defer_without_starting_child(
    tmp_path, monkeypatch, limit, reason
):
    class Clock(datetime):
        current = datetime.fromisoformat("2026-10-08T22:40:00+09:00")

        @classmethod
        def now(cls, tz=None):
            return cls.current

    elapsed = {"seconds": 0.0, "rss": 0, "owner": False}
    monkeypatch.setattr(A, "datetime", Clock)
    monkeypatch.setattr(A.time, "monotonic", lambda: elapsed["seconds"])
    monkeypatch.setattr(A, "supervisor_rss", lambda: elapsed["rss"])
    monkeypatch.setattr(A, "heavy_owner_running", lambda: elapsed["owner"])
    monkeypatch.setattr(A, "verify_installed_calendar", lambda _: True)
    monkeypatch.setattr(A, "discover_dates", lambda *a: [DAY])
    root = A.namespace(tmp_path)
    A.atomic(
        root / "installation.json",
        R.seal(
            dict(
                enabled=True,
                calendar_verified=True,
                next_main_preparation_clock_kst="07:35",
            )
        ),
    )
    A.atomic(root / DAY / "cursor.json", dict(status="completed"))

    def source_changed(*a):
        if limit == "wall":
            elapsed["seconds"] = 61.0
        elif limit == "memory":
            elapsed["rss"] = A.MEMORY_BYTES + 1
        elif limit == "window":
            Clock.current = datetime.fromisoformat("2026-10-09T08:01:00+09:00")
        else:
            elapsed["owner"] = True
        return True

    monkeypatch.setattr(A, "cursor_current", source_changed)
    monkeypatch.setattr(
        A,
        "supervise",
        lambda *a, **k: pytest.fail("child started after preflight limit"),
    )
    result = A.scheduled(tmp_path)
    assert result["status"] == "deferred_resource_or_window"
    assert result["reason"] == reason
    assert result["worker_started"] is False
    assert A.check_seal(A.read_json(root / "night_summary.json")) == result
    reservation = A.read_json(root / "nights/2026-10-08.json")
    assert reservation["attempts"] == 1
    assert reservation["reserved_seconds"] == 60
    assert not list((root / "attempts").glob("*.json"))


def test_empty_source_selection_publishes_own_summary_without_child(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        A,
        "night_window",
        lambda *a: (
            DAY,
            datetime.now(R.KST) + timedelta(hours=1),
            None,
        ),
    )
    monkeypatch.setattr(A, "verify_installed_calendar", lambda _: True)
    monkeypatch.setattr(A, "heavy_owner_running", lambda: False)
    monkeypatch.setattr(A, "discover_dates", lambda *a: [])
    monkeypatch.setattr(
        A, "supervise", lambda *a, **k: pytest.fail("empty source spawned child")
    )
    root = A.namespace(tmp_path)
    A.atomic(root / "installation.json", R.seal(dict(enabled=True)))
    result = A.scheduled(tmp_path)
    assert result["status"] == "valid_empty"
    assert result["worker_started"] is False
    assert A.check_seal(A.read_json(root / "night_summary.json")) == result


def test_append_cutoff_changed_during_read_never_seals(tmp_path, monkeypatch):
    data, p, _ = setup_sources(tmp_path, monkeypatch)
    original = A.trace_records

    def changing(*args, **kwargs):
        result = original(*args, **kwargs)
        with p.open("a") as f:
            f.write("{}\n")
        return result

    monkeypatch.setattr(A, "trace_records", changing)
    with pytest.raises(A.Deferred, match="source_cutoff_changed"):
        run_date(data)
    assert not list((A.namespace(data) / DAY).glob("*/terminal.json"))


def test_completed_projection_tamper_cannot_reuse_old_pass(tmp_path, monkeypatch):
    data, _, _ = setup_sources(tmp_path, monkeypatch)
    run_date(data)
    c = A.read_json(A.namespace(data) / DAY / "cursor.json")
    Path(c["partitions"][0]["path"]).write_text("{}")
    with pytest.raises(ValueError, match="projection_changed"):
        run_date(data)


def test_candidate_manifest_does_not_freeze_empty_first_day_forever(
    tmp_path, monkeypatch
):
    data, _, _ = setup_sources(tmp_path, monkeypatch)
    run_date(data)
    A.cumulative(data, stop_at=time.monotonic() + 15)
    assert not (A.namespace(data) / "fixed_candidates.json").exists()


def test_supervisor_reaps_spawned_descendant_even_if_leader_exits(tmp_path):
    marker = tmp_path / "descendant.pid"
    code = 'import subprocess,sys; p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(30)"]);open(sys.argv[1],"w").write(str(p.pid))'
    result = A.supervise(
        [sys.executable, "-c", code, str(marker)], seconds=2, gate=lambda: True
    )
    assert result["exit_code"] == 0
    child = int(marker.read_text())
    assert not Path("/proc", str(child)).exists()


def test_partial_tail_does_not_append_empty_partition_on_every_retry(
    tmp_path, monkeypatch
):
    data, p, _ = setup_sources(tmp_path, monkeypatch)
    p.write_text('{"partial":')
    for _ in range(2):
        with pytest.raises(A.Deferred):
            run_date(data)
    c = A.read_json(A.namespace(data) / DAY / "cursor.json")
    assert not c["partitions"]
    assert not c.get("source_ranges")


@pytest.mark.parametrize("compact", [False, True])
def test_stored_codec_uses_existing_projector_and_preserves_wire(
    compact, tmp_path, monkeypatch
):
    from src.engine.scalping import reversal_auxiliary_registry as G
    from src.engine.scalping import reversal_auxiliary_wire as W
    from src.engine.scalping import reversal_auxiliary_research_wire as OLD
    from src.tests.test_reversal_extended_policy import FIXTURES
    from src.engine.scalping import reversal_extended_union as U

    fixture = next(iter(FIXTURES.values()))
    snap = (fixture["event"], fixture["source"])
    original = G.definition(U.V1.ARMS[1], input_version=U.VERSION)
    policy = (
        G.compact_definition(original, research_wire_contract=OLD.contract())
        if compact
        else original
    )
    logical, prompt, _ = G.production_request(snap, policy)
    req = G.request(snap, policy)
    aliases = W.encode(logical)[2]
    raw = dict(
        assessed={aliases[s["ref"]]: True for s in logical["signals"]},
        screen=dict(
            verdict="PASS",
            risk="NO_BLOCKING_RISK",
            fact=aliases["observed_machine_signal"],
        ),
        confidence=50,
    )
    response = raw if compact else W.decode(raw, logical, policy["base_arm"])
    result = {"candidate_response": response}
    unchanged = copy.deepcopy(req)

    class Reader:
        receipts = {}

        def __init__(self, *a):
            pass

        def get(self, *a):
            return list(snap)

        def close(self):
            pass

    monkeypatch.setattr(A, "ReadObjects", Reader)
    inp, decoded, binding, _ = A.decode_stored_response(
        req, result, {"source_ref": {"snapshot_object": 1}}, tmp_path
    )
    assert inp == logical
    assert decoded["risk_verdict"] == "PASS"
    assert req == unchanged
    assert binding == G.binding(policy)
    if compact:
        req["candidate"]["logical_input_sha256"] = "wrong"
        with pytest.raises(ValueError):
            A.decode_stored_response(
                req, result, {"source_ref": {"snapshot_object": 1}}, tmp_path
            )


def test_optional_installer_mutates_only_its_tag_and_pins_install_code(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace

    original = "35 22 * * 1-5 bash /preopen # THRESHOLD_CYCLE_PREOPEN\n0 12 * * * bash /eod # EOD\n"
    calls = []
    installed = [original]
    A.namespace(tmp_path / "data").parent.mkdir(parents=True)

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        if "input" in kwargs:
            installed[0] = kwargs["input"]
        return SimpleNamespace(returncode=0, stdout=installed[0])

    monkeypatch.setattr(
        A,
        "alternate_schedule_census",
        lambda _: dict(status="observed_no_alternate_registration"),
    )
    monkeypatch.setattr(
        A, "selected_optional_code", lambda _: str(tmp_path / "release")
    )
    monkeypatch.setattr(A, "host_cron_zone", lambda: "UTC")
    assert (
        A.configure_optional_cron(tmp_path / "data", tmp_path, runner=runner)["status"]
        == "optional_cron_installed"
    )
    assert len(calls) == 3
    assert original in calls[1][1]["input"]
    assert calls[1][1]["input"].count(A.TAG) == 1
    cfg = A.check_seal(
        A.read_json(A.namespace(tmp_path / "data") / "installation.json")
    )
    assert cfg["installation_code_sha256"] == A.code_hash()
    assert cfg["cron_scope"] == "one_named_user"
    assert cfg["notify_enabled"] is False


def test_root_optional_installer_creates_namespace_for_cron_user(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import os

    owner = A.pwd.getpwuid(os.geteuid())
    root = A.namespace(tmp_path / "data")
    root.parent.mkdir(parents=True)
    original = "35 7 * * * bash /preopen # THRESHOLD_CYCLE_PREOPEN\n"
    installed = [original]
    ownership = []

    def runner(command, **kwargs):
        if "input" in kwargs:
            installed[0] = kwargs["input"]
        return SimpleNamespace(returncode=0, stdout=installed[0])

    monkeypatch.setattr(A.os, "geteuid", lambda: 0)
    monkeypatch.setattr(A.os, "chown", lambda *args: ownership.append(args))
    monkeypatch.setattr(A, "alternate_schedule_census", lambda _: {})
    monkeypatch.setattr(A, "selected_optional_code", lambda _: "reviewed")
    monkeypatch.setattr(A, "host_cron_zone", lambda: "Asia/Seoul")
    result = A.configure_optional_cron(
        tmp_path / "data", tmp_path, cron_user=owner.pw_name, runner=runner
    )
    assert result["status"] == "optional_cron_installed"
    assert (root, owner.pw_uid, owner.pw_gid) in ownership
    if owner.pw_uid:
        assert (root / "installation.json", owner.pw_uid, owner.pw_gid) in ownership
    assert root.stat().st_mode & 0o777 == 0o700


def test_optional_install_readback_failure_cannot_claim_installed(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace

    A.namespace(tmp_path / "data").parent.mkdir(parents=True)
    original = "35 7 * * * bash /preopen # THRESHOLD_CYCLE_PREOPEN\n"
    monkeypatch.setattr(A, "alternate_schedule_census", lambda _: {})
    monkeypatch.setattr(A, "selected_optional_code", lambda _: "reviewed")
    monkeypatch.setattr(A, "host_cron_zone", lambda: "Asia/Seoul")
    with pytest.raises(ValueError, match="readback_mismatch"):
        A.configure_optional_cron(
            tmp_path / "data",
            tmp_path,
            runner=lambda *a, **k: SimpleNamespace(returncode=0, stdout=original),
        )


def test_alternate_root_user_or_systemd_schedule_conflict_is_detected(tmp_path):
    spool = tmp_path / "spool"
    spool.mkdir()
    (spool / "root").write_text("40 12 * * * bash /other # " + A.TAG)
    with pytest.raises(ValueError, match="duplicate_optional"):
        A.alternate_schedule_census("ubuntu", spool=spool, etc=tmp_path / "etc")
    (spool / "root").unlink()
    (spool / "ubuntu").write_text("40 12 * * * bash /current # " + A.TAG)
    assert (
        A.alternate_schedule_census("ubuntu", spool=spool, etc=tmp_path / "etc")[
            "status"
        ]
        == "observed_no_alternate_registration"
    )


def test_unobservable_alternate_schedule_prevents_registration(tmp_path, monkeypatch):
    spool = tmp_path / "spool"
    spool.mkdir()
    (spool / "root").write_text("root cron")
    original = Path.read_text

    def read(p, *a, **k):
        if p.name == "root":
            raise PermissionError
        return original(p, *a, **k)

    monkeypatch.setattr(Path, "read_text", read)
    with pytest.raises(ValueError, match="unobservable"):
        A.alternate_schedule_census("ubuntu", spool=spool, etc=tmp_path / "etc")


def test_selected_optional_code_requires_all_reviewed_modules(tmp_path, monkeypatch):
    from src.engine.infrastructure import runtime_release_router as router

    monkeypatch.setattr(
        router, "selected_release", lambda _: (tmp_path / "missing", {})
    )
    with pytest.raises(ValueError, match="not_reviewed"):
        A.selected_optional_code(Path(__file__).resolve().parents[2])


def test_wrapper_routes_to_selected_immutable_root_without_main_start(tmp_path):
    import subprocess

    repo = Path(__file__).resolve().parents[2]
    workspace, release = tmp_path / "workspace", tmp_path / "release"
    marker = tmp_path / "argv.txt"
    for root in (workspace, release):
        (root / "deploy").mkdir(parents=True)
        (root / ".venv/bin").mkdir(parents=True)
        (root / "deploy/run_main_market_weakness_research_postclose.sh").write_bytes(
            (
                repo / "deploy/run_main_market_weakness_research_postclose.sh"
            ).read_bytes()
        )
    (workspace / ".venv/bin/python").write_text(
        '#!/bin/bash\nprintf "%s\\n" "' + str(release) + '"\n'
    )
    (release / ".venv/bin/python").write_text(
        '#!/bin/bash\nif [[ "$1" == "-I" ]]; then printf "%s\\n" "'
        + str(release)
        + '"; else printf "%s\\n" "$PWD" "$PYTHONPATH" "$@" > "'
        + str(marker)
        + '"; fi\n'
    )
    for root in (workspace, release):
        (root / ".venv/bin/python").chmod(0o755)
    (tmp_path / "shared").mkdir()
    (release / "data").symlink_to(tmp_path / "shared", target_is_directory=True)
    subprocess.run(
        [
            "bash",
            str(workspace / "deploy/run_main_market_weakness_research_postclose.sh"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    output = marker.read_text()
    assert str(release) in output
    assert A.MODULE in output
    assert "--scheduled" in output
    assert "bot" not in output
