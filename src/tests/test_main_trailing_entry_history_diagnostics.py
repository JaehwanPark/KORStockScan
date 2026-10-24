"""Native persisted causal OHLC prefixes remain diagnostic-only."""

from contextlib import closing
from copy import deepcopy
from datetime import datetime, timedelta
import json
import sqlite3

import pytest

from src.engine.automation import main_trailing_entry_history_diagnostics as diagnostic
from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.holding_window_generation import byte_generation
from src.engine.lifecycle.research_input_budget import Claim, health
from src.engine.scalping.pre_submit_delay_initial_policy import digest
from src.engine.scalping.trailing_situation_policy import entry_features
from src.trading.market import completed_history as history

DAY, ISO_DAY = "20261015", "2026-10-15"


def clock(value="09:10:00", day=ISO_DAY):
    return datetime.fromisoformat(day + "T" + value + "+09:00").timestamp()


def bars(count, *, start="09:00:00", day=ISO_DAY, high=105):
    began = datetime.fromisoformat(day + "T" + start + "+09:00")
    return [
        dict(
            source_timestamp=(began + timedelta(minutes=i)).strftime("%Y%m%d%H%M%S"),
            시가=100,
            고가=high,
            저가=98,
            현재가=101,
            거래량=1000,
        )
        for i in range(count)
    ]


def publish(
    root,
    rows,
    *,
    now=None,
    item="005930",
    scope=("real", "native-test"),
    session="unspecified",
    tag=None,
):
    now = clock() if now is None else now
    identity, receipt = history.key(scope, item, DAY, session), {}
    meta = dict(
        api_id="ka10080", request_code=item, rest_received_ts_ms=int(now * 1000)
    )
    if tag is not None:
        meta["synthetic_receipt_tag"] = tag
    assert history.publish(
        root, identity, rows, meta, now=now, consumption_receipt=receipt
    )
    return root / "runtime/main_minute_history" / DAY / "completed.sqlite3", receipt


def seal(path, body):
    body = {k: v for k, v in body.items() if k != "artifact_sha256"}
    value = {**body, "artifact_sha256": digest(body)}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False))
    return digest(value)


def position(
    identity="cf:one", *, at=None, kind="enter_pass_opportunity_cf", item="005930"
):
    return dict(
        position_key=identity,
        evidence_kind=kind,
        symbol="005930",
        item=item,
        route="krx_only",
        entry_at=clock("09:05:00") if at is None else at,
        automatic_management_allowed=False,
        entry_context={"status": "classification_source_gap"},
        situation_pin={"type": "BASE"},
    )


def fixture(tmp_path, positions=None):
    positions = [position()] if positions is None else positions
    source, root, output = tmp_path / "source", tmp_path / "input", tmp_path / "output"
    source.mkdir()
    root.mkdir()
    part = root / "part.json"
    part_sha = seal(
        part,
        dict(
            source_date=ISO_DAY, target_date="2026-10-16", positions=positions, paths={}
        ),
    )
    manifest = root / "manifest.json"
    seal(
        manifest,
        dict(
            schema="main_all_scope_exit_input_manifest_v2",
            source_date=ISO_DAY,
            target_date="2026-10-16",
            source_data_root=str(source),
            as_of=clock(),
            consumed_dates=[ISO_DAY],
            universe=[dict(symbol="005930", known_at=clock("08:00:00"), tradable=True)],
            universe_source_sha256="a" * 64,
            partitions_ref=storage.write_tree(
                root, [dict(path="part.json", artifact_sha256=part_sha)]
            ),
            population_ids_ref=storage.write_tree(
                root, [p["position_key"] for p in positions]
            ),
        ),
    )
    registration = tmp_path / "registration.json"
    seal(
        registration,
        dict(
            schema="main_trailing_followup_registration_v1",
            source_date=ISO_DAY,
            target_date="2026-10-16",
            as_of=clock(),
            input_manifest_path=str(manifest),
            input_manifest_generation=byte_generation(manifest),
            holdout_start_date=ISO_DAY,
            holdout_end_date=ISO_DAY,
            allowed_runtime_apply=False,
            runtime_effect=False,
            actual_pid_consumed=False,
            decision_authority="report_only",
            metric_contract=dict(
                primary_decision_metric="none",
                metric_role="funnel_count",
                decision_authority="report_only",
                sample_floor="diagnostic_no_promotion",
            ),
            diagnostics=dict(
                entry_history=dict(
                    output_root=str(output),
                    window_bars=120,
                    minimum_feature_bars=2,
                    features=list(diagnostic.FEATURES),
                    runtime_six_feature_classifier_ready=False,
                    original_runtime_consumption_proven=False,
                    spread_pct=None,
                    session_vwap=None,
                    selection_clock=diagnostic.SELECTION_CLOCK,
                    pattern_bins=dict(
                        range_pct_edges=[1.0, 2.0],
                        upward_efficient=dict(
                            return_pct_min=0.2, trend_efficiency_min=0.5
                        ),
                    ),
                )
            ),
        ),
    )
    return source, root, manifest, registration, output


def run(paths):
    source, root, manifest, registration, output = paths
    return diagnostic.run(
        registration, manifest, input_root=root, data_root=source, output_root=output
    )


def native_read(root, at, item="005930"):
    with Claim(0) as budget, diagnostic.minute._snapshot(root, DAY) as snapshot:
        with closing(diagnostic.EntryHistory(snapshot, DAY, {item}, budget)) as reader:
            return reader.read(item, at)


def test_native_producer_to_registered_report_preserves_population_scope_and_original_pins(
    tmp_path,
):
    positions = [
        position(),
        position("actual", kind="actual_completed"),
        position("alternative", kind="actual_entry_alternative_exit"),
        position("carry", at=clock("15:00:00", "2026-10-14"), kind="actual_completed"),
    ]
    paths = fixture(tmp_path, positions)
    path, early = publish(paths[0], bars(4), now=clock("09:04:00"))
    publish(paths[0], bars(10))  # Later current must not leak into entry.
    before = diagnostic.minute.carrier_generation(path)
    original = {p: p.read_bytes() for p in (paths[2], paths[3], paths[1] / "part.json")}
    report = run(paths)
    saved = json.loads((paths[4] / "report.json").read_text())
    assert saved == report and saved["artifact_sha256"] == digest(
        {k: v for k, v in report.items() if k != "artifact_sha256"}
    )
    assert (
        report["input_population_count"] == 4
        and report["population_count"] == 3
        and report["excluded_alternative_exit_count"] == 1
    )
    assert report["scope"]["symbol_count"] == 1 and report["scope"]["scope_count"] == 8
    rows = {r["identity"]: r for r in report["rows"]}
    assert (
        rows["carry"]["status"] == "audit_only"
        and rows["carry"]["reason"] == "entry_before_research_window"
    )
    assert rows["carry"]["entry_at"] == positions[-1]["entry_at"]
    for key in ("cf:one", "actual"):
        row = rows[key]
        assert row["status"] == "ohlc_partial_window" and row["window_bars"] == 4
        assert (
            row["source"]["revision_sha256"] == early["shared_history_revision_sha256"]
        )
        assert (
            row["source"]["available_at"] == clock("09:04:00")
            and row["chronological_partition"] == "holdout"
        )
        assert row["automatic_management_allowed"] is False
        assert (
            row["original_entry_context"] == positions[0]["entry_context"]
            and row["original_situation_pin"] == positions[0]["situation_pin"]
        )
        assert (
            row["spread_pct"] is row["session_vwap"] is row["vwap_distance_pct"] is None
        )
        assert (
            row["runtime_six_feature_classifier_ready"]
            is row["original_runtime_consumption_proven"]
            is False
        )
    assert report["reader_stats"]["native_full_revision_reads"] == 1
    assert report["reader_stats"]["full_revision_cache_hits"] == 1
    assert report["reader_stats"]["catalog_scopes_inspected"] == 1
    assert all(p.read_bytes() == raw for p, raw in original.items())
    assert (
        diagnostic.minute.carrier_generation(path) == before
        and health()["used_bytes"] == 0
    )
    with pytest.raises(ValueError, match="output_not_new"):
        run(paths)


def test_previous_day_only_prefix_is_real_and_not_replaced_by_current_future_revision(
    tmp_path,
):
    paths = fixture(tmp_path)
    prefix = bars(130, start="13:00:00", day="2026-10-14")
    _, early = publish(paths[0], prefix, now=clock("09:00:00"))
    publish(paths[0], prefix + bars(10))
    report = run(paths)
    row = report["rows"][0]
    assert row["source"]["revision_sha256"] == early["shared_history_revision_sha256"]
    assert row["full_120_bar_window"] is True and row["window_bars"] == 120
    assert (
        row["prior_date_bar_count"] == 120 and row["source_prior_date_bar_count"] == 130
    )
    assert row["last_bar_close_at"] == clock("15:10:00", "2026-10-14")
    assert row["last_completed_bar_age_seconds"] == clock("09:05:00") - clock(
        "15:10:00", "2026-10-14"
    )
    assert (
        row["same_day_internal_missing_minutes"] == 0
        and row["revision_age_seconds"] == 300
    )
    result, issue = diagnostic.minute.series(
        paths[0], DAY, "005930", as_of=clock("09:05:00")
    )
    assert result is None and issue == "minute_history_same_day_completed_bars_missing"


@pytest.mark.parametrize("count", [1, 2, 119, 120, 121])
def test_full_and_partial_window_are_separate_and_formulas_match_existing_owner(
    tmp_path, count
):
    paths = fixture(tmp_path)
    publish(
        paths[0], bars(count, start="12:00:00", day="2026-10-14"), now=clock("09:00:00")
    )
    row = run(paths)["rows"][0]
    assert row["window_bars"] == min(count, 120) and row["full_120_bar_window"] == (
        count >= 120
    )
    if count == 1:
        assert (
            row["features"] is None and row["reason"] == "fewer_than_two_completed_bars"
        )
    else:
        native, _ = native_read(paths[0], clock("09:05:00"))
        existing = entry_features(
            [
                {**r, "known_at": clock("09:00:00"), "route": "krx_only"}
                for r in native[-120:]
            ],
            anchor_at=clock("09:05:00"),
            ask=102,
            bid=100,
            session_vwap=101,
            source_sha256="a" * 64,
            expected_route="krx_only",
        )
        assert existing["status"] == "ready" and row["features"] == {
            k: existing["features"][k] for k in diagnostic.FEATURES
        }
    assert row["runtime_six_feature_classifier_ready"] is False


def test_catalog_reader_matches_native_minute_selection_and_normalization(tmp_path):
    publish(tmp_path, bars(2), now=clock("09:02:00"), session="PRE")
    publish(tmp_path, bars(4), now=clock("09:04:00"), session="REGULAR")
    publish(tmp_path, bars(10), session="CLOSED")
    rows, source = native_read(tmp_path, clock("09:05:00"))
    old, issue = diagnostic.minute.series(
        tmp_path, DAY, "005930", as_of=clock("09:05:00")
    )
    assert issue is None and source["revision_sha256"] == old["revision_sha256"]
    assert source["source_identity"] == old["source_identity"]
    assert (
        source["eligible_acquisition_sessions"] == old["eligible_acquisition_sessions"]
    )
    assert [(r["opened_at"], r["low"], r["high"]) for r in rows] == old["bars"]


@pytest.mark.parametrize(
    "variant", ["future", "item", "auth", "equal_clock", "adjustment"]
)
def test_wrong_or_ambiguous_source_cannot_supply_features(tmp_path, variant):
    paths = fixture(tmp_path)
    source = paths[0]
    path, _ = publish(
        source,
        bars(4),
        now=clock("09:06:00") if variant == "future" else clock("09:04:00"),
        item="005930_NX" if variant == "item" else "005930",
    )
    if variant == "auth":
        publish(
            source,
            bars(4),
            now=clock("09:04:00"),
            scope=("demo", "other"),
            session="OTHER",
        )
    if variant == "equal_clock":
        publish(source, bars(4, high=106), now=clock("09:04:00"), session="OTHER")
    if variant == "adjustment":
        with closing(sqlite3.connect(path)) as db, db:
            scope, old, blob = db.execute(
                "SELECT scope,hash,manifest FROM revisions"
            ).fetchone()
            changed = history._unpack(blob)
            changed["identity"]["adjustment"] = "unadjusted"
            new_scope = history._digest(changed["identity"])
            new = history._digest(changed)
            db.execute(
                "UPDATE revisions SET scope=?,hash=?,manifest=? WHERE hash=?",
                (new_scope, new, history._pack(changed), old),
            )
            db.execute(
                "UPDATE current SET scope=?,revision=? WHERE scope=?",
                (new_scope, new, scope),
            )
    row = run(paths)["rows"][0]
    assert row["status"] == "source_gap" and row["features"] is row["source"] is None
    assert row["spread_pct"] is row["session_vwap"] is None and "window_bars" not in row
    assert (
        row["reason"]
        == {
            "future": "entry_history_no_local_revision_known_by_entry",
            "item": "entry_history_no_local_revision_known_by_entry",
            "auth": "entry_history_exact_scope_ambiguous",
            "equal_clock": "entry_history_same_clock_revision_conflict",
            "adjustment": "entry_history_chart_contract_invalid",
        }[variant]
    )


def test_missing_local_carrier_is_unknown_not_official_impossible(tmp_path):
    report = run(fixture(tmp_path))
    assert report["rows"][0]["reason"] == "minute_history_not_stored"
    assert report["local_source_gap_proves_official_unavailability"] is False
    assert list(report["source_carrier_generations"].values()) == [{"missing": True}]


@pytest.mark.parametrize(
    "bad", [True, "123", float("nan"), float("inf"), -1, 0, 10**400]
)
def test_clock_rejects_bool_strings_nonfinite_and_overflow(bad):
    with pytest.raises(ValueError, match="clock_invalid"):
        diagnostic._clock(bad)


@pytest.mark.parametrize("mutation", ["nan", "bool", "forming", "reverse", "duplicate"])
def test_native_read_return_is_checked_for_semantically_invalid_bars(
    tmp_path, monkeypatch, mutation
):
    paths = fixture(tmp_path)
    publish(paths[0], bars(4), now=clock("09:04:00"))
    original = history.read

    def altered(*args, **kwargs):
        rows, meta = original(*args, **kwargs)
        if mutation in {"nan", "bool"}:
            rows[1]["현재가"] = float("nan") if mutation == "nan" else True
        if mutation == "forming":
            rows[-1]["source_timestamp"] = "20261015090500"
        if mutation == "reverse":
            rows[1], rows[2] = rows[2], rows[1]
        if mutation == "duplicate":
            rows[2] = deepcopy(rows[1])
        return rows, meta

    monkeypatch.setattr(history, "read", altered)
    row = run(paths)["rows"][0]
    assert row["status"] == "source_gap" and row["features"] is row["source"] is None
    assert "window_bars" not in row and row["spread_pct"] is None


def test_mid_read_original_carrier_mutation_rejects_publication(tmp_path, monkeypatch):
    paths = fixture(tmp_path)
    publish(paths[0], bars(4), now=clock("09:04:00"))
    original = history.read

    def mutated(*args, **kwargs):
        result = original(*args, **kwargs)
        publish(paths[0], bars(10))
        return result

    monkeypatch.setattr(history, "read", mutated)
    with pytest.raises(ValueError, match="provenance_changed"):
        run(paths)
    assert not paths[4].exists() and health()["used_bytes"] == 0


@pytest.mark.parametrize(
    "target", ["manifest", "registration", "partition", "carrier", "missing_carrier"]
)
def test_final_publication_rechecks_source_generations(tmp_path, monkeypatch, target):
    paths = fixture(tmp_path)
    if target != "missing_carrier":
        publish(paths[0], bars(4), now=clock("09:04:00"))
    original = diagnostic.build

    def changed(*args, **kwargs):
        report = original(*args, **kwargs)
        if target in {"carrier", "missing_carrier"}:
            publish(paths[0], bars(10))
        else:
            path = {
                "manifest": paths[2],
                "registration": paths[3],
                "partition": paths[1] / "part.json",
            }[target]
            path.write_text(path.read_text() + "\n")
        return report

    monkeypatch.setattr(diagnostic, "build", changed)
    with pytest.raises(ValueError, match="prepublication_"):
        run(paths)
    assert not paths[4].exists()


def test_metadata_size_ceiling_checked_before_hash_or_decode(tmp_path, monkeypatch):
    paths = fixture(tmp_path)
    monkeypatch.setattr(diagnostic, "MAX_METADATA_BYTES", 1)
    monkeypatch.setattr(
        diagnostic, "byte_generation", lambda _: pytest.fail("unadmitted metadata hash")
    )
    with pytest.raises(ValueError, match="metadata_budget_invalid"):
        run(paths)


def test_registration_must_bind_exact_input_generation_and_diagnostic_only_scope(
    tmp_path,
):
    paths = fixture(tmp_path)
    value = json.loads(paths[3].read_text())
    value["runtime_effect"] = True
    seal(paths[3], value)
    with pytest.raises(ValueError, match="registration_contract_invalid"):
        run(paths)
    value["runtime_effect"] = False
    value["input_manifest_generation"]["sha256"] = "f" * 64
    seal(paths[3], value)
    with pytest.raises(ValueError, match="registration_contract_invalid"):
        run(paths)
    assert not paths[4].exists()


def test_forming_native_bar_is_excluded_and_gap_is_only_between_observed_bars(tmp_path):
    paths = fixture(tmp_path)
    publish(
        paths[0],
        [bars(4)[0], bars(4)[3]] + bars(1, start="09:04:00"),
        now=clock("09:04:00"),
    )
    row = run(paths)["rows"][0]
    assert row["window_bars"] == 2 and row["last_bar_close_at"] == clock("09:04:00")
    assert (
        row["same_day_internal_missing_minutes"] == 2
        and row["last_completed_bar_age_seconds"] == 60
    )


@pytest.mark.parametrize(
    "at,expected",
    [
        ("09:03:59", "source_gap"),
        ("09:04:00", "ohlc_partial_window"),
        ("09:11:00", "source_gap"),
    ],
)
def test_revision_entry_and_report_cutoffs_are_separate(tmp_path, at, expected):
    paths = fixture(tmp_path, [position(at=clock(at))])
    publish(paths[0], bars(4), now=clock("09:04:00"))
    row = run(paths)["rows"][0]
    assert row["status"] == expected
    if expected == "ohlc_partial_window":
        assert (
            row["revision_age_seconds"] == 0
            and row["last_completed_bar_age_seconds"] == 0
        )
    else:
        assert row["features"] is None


def test_entry_after_source_period_before_report_cutoff_is_census_only(
    tmp_path, monkeypatch
):
    original = position("future-source", at=clock("09:00:00", "2026-10-16"))
    paths = fixture(tmp_path, [original])
    manifest = json.loads(paths[2].read_text())
    manifest["as_of"] = clock("09:00:00", "2026-10-18")
    seal(paths[2], manifest)
    registration = json.loads(paths[3].read_text())
    registration["as_of"] = manifest["as_of"]
    registration["input_manifest_generation"] = byte_generation(paths[2])
    seal(paths[3], registration)
    monkeypatch.setattr(
        diagnostic.minute,
        "_snapshot",
        lambda *a: pytest.fail("out-of-window source opened"),
    )
    report = run(paths)
    row = report["rows"][0]
    assert report["input_population_count"] == report["population_count"] == 1
    assert (
        row["identity"] == original["position_key"]
        and row["entry_at"] == original["entry_at"]
    )
    assert (
        row["status"] == "audit_only" and row["reason"] == "entry_after_research_window"
    )
    assert (
        row["features"] is row["source"] is None
        and "chronological_partition" not in row
    )
    assert row["research_entry_window_end_exclusive_at"] == clock(
        "00:00:00", "2026-10-16"
    )
    assert (
        row["original_entry_context"] == original["entry_context"]
        and row["original_situation_pin"] == original["situation_pin"]
    )


def test_resealed_native_receipt_bool_cannot_alias_sql_numeric_clock(tmp_path):
    paths = fixture(tmp_path)
    path, _ = publish(paths[0], bars(4), now=clock("09:04:00"))
    with closing(sqlite3.connect(path)) as db, db:
        old, blob = db.execute("SELECT hash,manifest FROM revisions").fetchone()
        changed = history._unpack(blob)
        changed["first_receipt"]["received_at"] = True
        new = history._digest(changed)
        db.execute(
            "UPDATE revisions SET hash=?,available=1,manifest=? WHERE hash=?",
            (new, history._pack(changed), old),
        )
        db.execute("UPDATE current SET revision=? WHERE revision=?", (new, old))
    row = run(paths)["rows"][0]
    assert (
        row["status"] == "source_gap" and row["reason"] == "entry_history_clock_invalid"
    )
    assert row["features"] is None


def test_resource_overflow_never_becomes_a_successful_empty_report(
    tmp_path, monkeypatch
):
    from src.engine.lifecycle import research_input_budget

    paths = fixture(tmp_path)
    publish(paths[0], bars(4), now=clock("09:04:00"))
    monkeypatch.setattr(research_input_budget, "LIMIT_BYTES", 1024 * 1024)
    with pytest.raises(ValueError, match="shared_research_budget"):
        run(paths)
    assert not paths[4].exists() and health()["used_bytes"] == 0


@pytest.mark.parametrize("post_clean", [0, 1, 2])
def test_clean_boundary_filters_feature_input_without_discarding_native_prefix(
    tmp_path, post_clean
):
    paths = fixture(tmp_path)
    source = bars(2, start="23:58:00", day="2026-06-04") + bars(
        post_clean, start="00:00:00", day="2026-06-05"
    )
    _, receipt = publish(paths[0], source, now=clock("09:04:00"))
    row = run(paths)["rows"][0]
    assert row["source"]["revision_sha256"] == receipt["shared_history_revision_sha256"]
    assert row["source"]["source_completed_bar_count"] == 2 + post_clean
    assert (
        row["source_pre_clean_bar_count"] == 2
        and row["eligible_clean_completed_bar_count"] == post_clean
    )
    assert row["window_bars"] == post_clean and row["full_120_bar_window"] is False
    assert row["feature_clean_baseline_start_at"] == clock("00:00:00", "2026-06-05")
    if post_clean:
        assert row["first_bar_open_at"] == clock("00:00:00", "2026-06-05")
    else:
        assert (
            row["status"] == "source_gap"
            and row["reason"] == "entry_history_no_clean_completed_bars"
        )
        assert (
            row["first_bar_open_at"]
            is row["last_bar_close_at"]
            is row["last_completed_bar_age_seconds"]
            is None
        )
    assert (row["features"] is not None) == (post_clean >= 2)


def test_native_plain_json_bar_size_admitted_before_public_decode(
    tmp_path, monkeypatch
):
    paths = fixture(tmp_path)
    large = [{**row, "extra": "x" * (2 * 1024 * 1024)} for row in bars(2)]
    publish(paths[0], large, now=clock("09:04:00"))
    monkeypatch.setattr(
        history, "read", lambda *a, **kw: pytest.fail("oversize native bar decoded")
    )
    with pytest.raises(ValueError, match="shared_research_budget"):
        run(paths)
    assert not paths[4].exists() and health()["used_bytes"] == 0


def test_native_size_admission_counts_utf8_bytes_for_sqlite_text_storage(tmp_path):
    paths = fixture(tmp_path)
    path, _ = publish(
        paths[0],
        [{**row, "extra": "한" * 100} for row in bars(2)],
        now=clock("09:04:00"),
    )
    expected = 0
    with closing(sqlite3.connect(path)) as db, db:
        for fingerprint, content in db.execute(
            "SELECT hash,content FROM bars"
        ).fetchall():
            text = json.dumps(json.loads(content), ensure_ascii=False)
            expected += len(text.encode())
            db.execute("UPDATE bars SET content=? WHERE hash=?", (text, fingerprint))
    report = run(paths)
    assert report["rows"][0]["window_bars"] == 2
    assert report["reader_stats"]["admitted_native_bar_json_bytes"] == expected


@pytest.mark.parametrize(
    "field",
    [
        "actual_pid_consumed",
        "original_runtime_consumption_proven",
        "selection_clock",
        "primary_decision_metric",
        "metric_role",
        "decision_authority",
        "sample_floor",
    ],
)
def test_resealed_registration_cannot_redefine_causal_selection_or_metric_authority(
    tmp_path, field
):
    paths = fixture(tmp_path)
    registration = json.loads(paths[3].read_text())
    if field == "actual_pid_consumed":
        registration[field] = True
    elif field in {"original_runtime_consumption_proven", "selection_clock"}:
        registration["diagnostics"]["entry_history"][field] = (
            True if field.endswith("proven") else "latest_at_report_cutoff"
        )
    else:
        registration["metric_contract"][field] = "runtime_apply"
    seal(paths[3], registration)
    with pytest.raises(ValueError, match="registration_"):
        run(paths)
    assert not paths[4].exists()


@pytest.mark.parametrize("conflicting", [False, True])
def test_same_clock_many_revisions_stream_at_most_two_decoded_manifests(
    tmp_path, monkeypatch, conflicting
):
    import weakref

    class Tracked(dict):
        pass

    refs = []
    live = []
    decode = diagnostic.EntryHistory._decode

    def tracked(self, *args):
        result = Tracked(decode(self, *args))
        refs.append(weakref.ref(result))
        live.append(sum(ref() is not None for ref in refs))
        return result

    for index in range(20):
        publish(
            tmp_path,
            bars(4, high=105 + index % 2 if conflicting else 105),
            now=clock("09:04:00"),
            session="SAME" if conflicting else f"S{index}",
            tag=str(index) + "x" * (64 * 1024),
        )
    monkeypatch.setattr(diagnostic.EntryHistory, "_decode", tracked)
    if conflicting:
        with pytest.raises(ValueError, match="same_clock_revision_conflict"):
            native_read(tmp_path, clock("09:05:00"))
    else:
        rows, source = native_read(tmp_path, clock("09:05:00"))
        assert len(rows) == 4 and source["available_at"] == clock("09:04:00")
    assert len(refs) == (21 if conflicting else 40) and max(live) <= 2


def test_partition_and_original_position_released_before_carrier_read(
    tmp_path, monkeypatch
):
    import weakref

    class Tracked(dict):
        pass

    paths = fixture(tmp_path)
    publish(paths[0], bars(4), now=clock("09:04:00"))
    original = diagnostic.minute._partitions
    checked = []

    def wrapped(*args):
        for path, generation, part in original(*args):
            holder = Tracked(part)
            holder["positions"] = [Tracked(p) for p in part["positions"]]
            references = [weakref.ref(holder)] + [
                weakref.ref(p) for p in holder["positions"]
            ]
            yield path, generation, holder
            del holder
            assert all(ref() is None for ref in references)
            checked.append(True)

    monkeypatch.setattr(diagnostic.minute, "_partitions", wrapped)
    row = run(paths)["rows"][0]
    assert checked == [True] and row["original_entry_context"] == {
        "status": "classification_source_gap"
    }


def test_newer_revision_resolves_older_clock_conflict_without_leaking_past_entry(
    tmp_path,
):
    publish(tmp_path, bars(2), now=clock("09:02:00"), session="PRE")
    publish(tmp_path, bars(2, high=106), now=clock("09:02:00"), session="PRE")
    _, latest = publish(tmp_path, bars(4), now=clock("09:04:00"), session="REGULAR")
    with pytest.raises(ValueError, match="same_clock_revision_conflict"):
        native_read(tmp_path, clock("09:03:00"))
    rows, source = native_read(tmp_path, clock("09:05:00"))
    assert (
        len(rows) == 4
        and source["revision_sha256"] == latest["shared_history_revision_sha256"]
    )


def test_scope_budget_tracks_current_registered_route_width(tmp_path, monkeypatch):
    paths = fixture(tmp_path)
    routes = deepcopy(diagnostic.scope_owner.ROUTES)
    bucket = next(iter(routes))
    routes[bucket] = tuple(routes[bucket]) + ("research_test_route",)
    monkeypatch.setattr(diagnostic.scope_owner, "ROUTES", routes)
    seen = []
    original = diagnostic.Claim.__init__

    def admitted(self, size):
        seen.append(size)
        original(self, size)

    monkeypatch.setattr(diagnostic.Claim, "__init__", admitted)
    report = run(paths)
    assert report["scope"]["scope_count"] == 9 and 9 * 512 in seen


def test_direct_dependency_generation_is_bound_and_rechecked(tmp_path, monkeypatch):
    paths = fixture(tmp_path)
    expected = {
        diagnostic.scope_owner.__file__,
        diagnostic.storage.__file__,
        diagnostic.sys.modules[
            diagnostic.research_entry_window_start.__module__
        ].__file__,
        diagnostic.sys.modules[diagnostic._sealed.__module__].__file__,
        diagnostic.sys.modules[diagnostic.Claim.__module__].__file__,
    }
    report = diagnostic.build(
        paths[2], input_root=paths[1], data_root=paths[0], registration_path=paths[3]
    )
    assert expected <= set(report["code_generations"])
    original = diagnostic.byte_generation
    calls = 0

    def changed(path):
        nonlocal calls
        value = original(path)
        if str(path) == diagnostic.scope_owner.__file__:
            calls += 1
            if calls > 1:
                return {**value, "sha256": "f" * 64}
        return value

    monkeypatch.setattr(diagnostic, "byte_generation", changed)
    with pytest.raises(ValueError, match="consumed_generation_changed"):
        run(paths)
    assert not paths[4].exists()
